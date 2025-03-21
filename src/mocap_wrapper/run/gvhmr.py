# https://github.com/zju3dv/GVHMR/blob/main/tools/demo/demo.py
from json import load
from typing import Literal, Sequence, Set, Union
import gc
import time
import inspect
import cv2
import torch
import pytorch_lightning as pl
import numpy as np
import argparse
from hmr4d.utils.pylogger import Log
import hydra
from hydra import initialize_config_module, compose
from pathlib import Path
from pytorch3d.transforms import quaternion_to_matrix

from hmr4d.configs import register_store_gvhmr
from hmr4d.utils.video_io_utils import (
    get_video_lwh,
    read_video_np,
    save_video,
    merge_videos_horizontal,
    get_writer,
    get_video_reader,
)
from hmr4d.utils.seq_utils import (  # patched
    get_frame_id_list_from_mask,
    linear_interpolate_frame_ids,
    frame_id_to_mask,
    rearrange_by_mask,
)
from hmr4d.utils.vis.cv2_utils import draw_bbx_xyxy_on_image_batch, draw_coco17_skeleton_batch

from hmr4d.utils.preproc import Tracker, Extractor, VitPoseExtractor, SimpleVO

from hmr4d.utils.geo.hmr_cam import get_bbx_xys_from_xyxy, estimate_K, convert_K_to_K4, create_camera_sensor
from hmr4d.utils.geo_transform import compute_cam_angvel
from hmr4d.model.gvhmr.gvhmr_pl_demo import DemoPL
from hmr4d.utils.net_utils import detach_to_cpu, to_cuda, moving_average_smooth  # patched
from hmr4d.utils.smplx_utils import make_smplx
from hmr4d.utils.vis.renderer import Renderer, get_global_cameras_static, get_ground_params_from_points
from tqdm import tqdm
from hmr4d.utils.geo_transform import apply_T_on_points, compute_T_ayfz2ay
from einops import einsum, rearrange


CRF = 23  # 17 is lossless, every +6 halves the mp4 size
person_count = None


def vram_gb(): return torch.cuda.memory_allocated() / 1024 ** 3


def free_ram():
    vram_before = vram_gb()

    stack = inspect.stack()
    caller = stack[1]
    gc.collect()
    torch.cuda.empty_cache()

    vram_release = vram_gb() - vram_before
    msg = f"[Free VRAM] {vram_release:.2f} GB at\t{caller.filename}:{caller.lineno}"
    if vram_release < -0.01:
        Log.info(msg)
    elif vram_release > 0.01:
        Log.warning(msg)
    else:
        Log.error(f'(DEBUG: Need removed) {msg}')


def load_yolo_track(cfg):
    global person_count
    file = cfg.paths.yolo_track + '.npz'

    data = np.load(file, allow_pickle=True)
    id_to_frame_ids = data['id_to_frame_ids'].item()
    id_to_bbx_xyxys = data['id_to_bbx_xyxys'].item()
    id_sorted = data['id_sorted']

    person_count = len(id_sorted)
    if not person_count:
        Log.info(f'How many people in the video? {person_count}')
    return id_to_frame_ids, id_to_bbx_xyxys, id_sorted


def get_one_track_patch(self, video_path, cfg):
    track_path = cfg.paths.yolo_track + '.npz'
    if Path(track_path).exists():
        id_to_frame_ids, id_to_bbx_xyxys, id_sorted = load_yolo_track(cfg)
    else:
        # track
        track_history = self.track(video_path)

        # parse track_history & use top1 track
        id_to_frame_ids, id_to_bbx_xyxys, id_sorted = self.sort_track_length(track_history, video_path)
        np.savez_compressed(cfg.paths.yolo_track, id_to_frame_ids=id_to_frame_ids, id_to_bbx_xyxys=id_to_bbx_xyxys, id_sorted=id_sorted)
    track_id = id_sorted[cfg.person]
    frame_ids = torch.tensor(id_to_frame_ids[track_id])  # (N,)
    bbx_xyxys = torch.tensor(id_to_bbx_xyxys[track_id])  # (N, 4)

    # interpolate missing frames
    mask = frame_id_to_mask(frame_ids, get_video_lwh(video_path)[0])
    bbx_xyxy_one_track = rearrange_by_mask(bbx_xyxys, mask)  # (F, 4), missing filled with 0
    missing_frame_id_list = get_frame_id_list_from_mask(~mask)  # list of list
    bbx_xyxy_one_track = linear_interpolate_frame_ids(bbx_xyxy_one_track, missing_frame_id_list)
    assert (bbx_xyxy_one_track.sum(1) != 0).all()

    bbx_xyxy_one_track = moving_average_smooth(bbx_xyxy_one_track, window_size=5, dim=0)
    bbx_xyxy_one_track = moving_average_smooth(bbx_xyxy_one_track, window_size=5, dim=0)

    return bbx_xyxy_one_track


Tracker.get_one_track = get_one_track_patch  # patched


def parse_args_to_cfg():
    # Put all args to cfg
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, default="inputs/demo/dance_3.mp4")
    parser.add_argument("--output_root", type=str, default='output/demo', help="by default to output/demo")
    parser.add_argument("-s", "--static_cam", action="store_true", help="If true, skip DPVO")
    parser.add_argument("--use_dpvo", action="store_true", help="If true, use DPVO. By default not using DPVO.")
    parser.add_argument(
        "--f_mm",
        type=int,
        default=None,
        help="Focal length of fullframe camera in mm. Leave it as None to use default values."
        "For iPhone 15p, the [0.5x, 1x, 2x, 3x] lens have typical values [13, 24, 48, 77]."
        "If the camera zoom in a lot, you can try 135, 200 or even larger values.",
    )
    parser.add_argument("--render", action="store_true", help="render the incam/global result video")
    parser.add_argument("-p", "--persons", type=str, help="List of persons to process, e.g. '0,1,2'")
    parser.add_argument("--verbose", action="store_true", help="If true, draw intermediate results")
    args = parser.parse_args()

    # Input
    video_path = Path(args.video)
    assert video_path.exists(), f"Video not found at {video_path}"
    length, width, height = get_video_lwh(video_path)
    Log.info(f"[Input]: {video_path}")
    Log.info(f"(L, W, H) = ({length}, {width}, {height})")
    # Cfg
    with initialize_config_module(version_base="1.3", config_module=f"hmr4d.configs"):
        overrides = [
            f"video_name='{video_path.stem}'",
            f"static_cam={args.static_cam}",
            f"verbose={args.verbose}",
            f"use_dpvo={args.use_dpvo}",
            f"person=0",    # u need to override with `cfg.person = 1`
            f"+render={args.render}",
        ]
        if args.f_mm is not None:
            overrides.append(f"f_mm={args.f_mm}")
        if args.persons is not None:
            overrides.append(f"persons={{{args.persons}}}")

        # Allow to change output root
        if args.output_root is not None:
            overrides.append(f"output_root={args.output_root}")
        register_store_gvhmr()
        cfg = compose(config_name="demo", overrides=overrides)

    # Output
    Log.info(f"[Output Dir]: {cfg.output_dir}")
    Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.preprocess_dir).mkdir(parents=True, exist_ok=True)

    # Copy raw-input-video to video_path
    Log.info(f"[Copy Video] {video_path} -> {cfg.video_path}")
    if not Path(cfg.video_path).exists() or get_video_lwh(video_path)[0] != get_video_lwh(cfg.video_path)[0]:
        reader = get_video_reader(video_path)
        writer = get_writer(cfg.video_path, fps=30, crf=CRF)
        for img in tqdm(reader, total=get_video_lwh(video_path)[0], desc=f"Copy"):
            writer.write_frame(img)
        writer.close()
        reader.close()

    return cfg


@torch.no_grad()
def run_preprocess(cfg):
    Log.info(f"[Preprocess] Start!")
    tic = Log.time()
    video_path = cfg.video_path
    paths = cfg.paths
    static_cam = cfg.static_cam
    verbose = cfg.verbose

    # Get bbx tracking result
    if not Path(paths.bbx).exists():
        tracker = Tracker()
        bbx_xyxy = tracker.get_one_track(video_path, cfg).float()  # (L, 4)
        bbx_xys = get_bbx_xys_from_xyxy(bbx_xyxy, base_enlarge=1.2).float()  # (L, 3) apply aspect ratio and enlarge
        torch.save({"bbx_xyxy": bbx_xyxy, "bbx_xys": bbx_xys}, paths.bbx)
        del tracker
    else:
        bbx_xys = torch.load(paths.bbx)["bbx_xys"]
        Log.info(f"[Preprocess] bbx (xyxy, xys) from {paths.bbx}")
    if verbose:
        video = read_video_np(video_path)
        bbx_xyxy = torch.load(paths.bbx)["bbx_xyxy"]
        video_overlay = draw_bbx_xyxy_on_image_batch(bbx_xyxy, video)
        save_video(video_overlay, cfg.paths.bbx_xyxy_video_overlay)

    free_ram()

    # Get VitPose
    if not Path(paths.vitpose).exists():
        vitpose_extractor = VitPoseExtractor()
        vitpose = vitpose_extractor.extract(video_path, bbx_xys)
        torch.save(vitpose, paths.vitpose)
        del vitpose_extractor
    else:
        vitpose = torch.load(paths.vitpose)
        Log.info(f"[Preprocess] vitpose from {paths.vitpose}")
    if verbose:
        video = read_video_np(video_path)
        video_overlay = draw_coco17_skeleton_batch(video, vitpose, 0.5)
        save_video(video_overlay, paths.vitpose_video_overlay)

    # Get vit features
    if not Path(paths.vit_features).exists():
        extractor = Extractor()
        vit_features = extractor.extract_video_features(video_path, bbx_xys)
        torch.save(vit_features, paths.vit_features)
        del extractor
    else:
        Log.info(f"[Preprocess] vit_features from {paths.vit_features}")

    # Get visual odometry results
    if not static_cam:  # use slam to get cam rotation
        if not Path(paths.slam).exists():
            if not cfg.use_dpvo:
                simple_vo = SimpleVO(cfg.video_path, scale=0.5, step=8, method="sift", f_mm=cfg.f_mm)
                vo_results = simple_vo.compute()  # (L, 4, 4), numpy
                torch.save(vo_results, paths.slam)
            else:  # DPVO
                from hmr4d.utils.preproc.slam import SLAMModel

                length, width, height = get_video_lwh(cfg.video_path)
                K_fullimg = estimate_K(width, height)
                intrinsics = convert_K_to_K4(K_fullimg)
                slam = SLAMModel(video_path, width, height, intrinsics, buffer=4000, resize=0.5)
                bar = tqdm(total=length, desc="DPVO")
                while True:
                    ret = slam.track()
                    if ret:
                        bar.update()
                    else:
                        break
                slam_results = slam.process()  # (L, 7), numpy
                torch.save(slam_results, paths.slam)
        else:
            Log.info(f"[Preprocess] slam results from {paths.slam}")

    Log.info(f"[Preprocess] End. Time elapsed: {Log.time()-tic:.2f}s")


def load_data_dict(cfg):
    paths = cfg.paths
    length, width, height = get_video_lwh(cfg.video_path)
    if cfg.static_cam:
        R_w2c = torch.eye(3).repeat(length, 1, 1)
    else:
        traj = torch.load(cfg.paths.slam)
        if cfg.use_dpvo:  # DPVO
            traj_quat = torch.from_numpy(traj[:, [6, 3, 4, 5]])
            R_w2c = quaternion_to_matrix(traj_quat).mT
        else:  # SimpleVO
            R_w2c = torch.from_numpy(traj[:, :3, :3])
    if cfg.f_mm is not None:
        K_fullimg = create_camera_sensor(width, height, cfg.f_mm)[2].repeat(length, 1, 1)
    else:
        K_fullimg = estimate_K(width, height).repeat(length, 1, 1)

    data = {
        "length": torch.tensor(length),
        "bbx_xys": torch.load(paths.bbx)["bbx_xys"],
        "kp2d": torch.load(paths.vitpose),
        "K_fullimg": K_fullimg,
        "cam_angvel": compute_cam_angvel(R_w2c),
        "f_imgseq": torch.load(paths.vit_features),
    }
    return data


def render_incam(cfg):
    incam_video_path = Path(cfg.paths.incam_video)
    if incam_video_path.exists():
        Log.info(f"[Render Incam] Video already exists at {incam_video_path}")
        return

    pred = torch.load(cfg.paths.hmr4d_results)
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    faces_smpl = make_smplx("smpl").faces

    # smpl
    smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
    pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])

    # -- rendering code -- #
    video_path = cfg.video_path
    length, width, height = get_video_lwh(video_path)
    K = pred["K_fullimg"][0]

    # renderer
    renderer = Renderer(width, height, device="cuda", faces=faces_smpl, K=K)
    reader = get_video_reader(video_path)  # (F, H, W, 3), uint8, numpy
    bbx_xys_render = torch.load(cfg.paths.bbx)["bbx_xys"]

    # -- render mesh -- #
    verts_incam = pred_c_verts
    writer = get_writer(incam_video_path, fps=30, crf=CRF)
    for i, img_raw in tqdm(enumerate(reader), total=get_video_lwh(video_path)[0], desc=f"Rendering Incam"):
        img = renderer.render_mesh(verts_incam[i].cuda(), img_raw, [0.8, 0.8, 0.8])

        # # bbx
        # bbx_xys_ = bbx_xys_render[i].cpu().numpy()
        # lu_point = (bbx_xys_[:2] - bbx_xys_[2:] / 2).astype(int)
        # rd_point = (bbx_xys_[:2] + bbx_xys_[2:] / 2).astype(int)
        # img = cv2.rectangle(img, lu_point, rd_point, (255, 178, 102), 2)

        writer.write_frame(img)
    writer.close()
    reader.close()


def render_global(cfg):
    global_video_path = Path(cfg.paths.global_video)
    if global_video_path.exists():
        Log.info(f"[Render Global] Video already exists at {global_video_path}")
        return

    debug_cam = False
    pred = torch.load(cfg.paths.hmr4d_results)
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    faces_smpl = make_smplx("smpl").faces
    J_regressor = torch.load("hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

    # smpl
    smplx_out = smplx(**to_cuda(pred["smpl_params_global"]))
    pred_ay_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])

    def move_to_start_point_face_z(verts):
        "XZ to origin, Start from the ground, Face-Z"
        # position
        verts = verts.clone()  # (L, V, 3)
        offset = einsum(J_regressor, verts[0], "j v, v i -> j i")[0]  # (3)
        offset[1] = verts[:, :, [1]].min()
        verts = verts - offset
        # face direction
        T_ay2ayfz = compute_T_ayfz2ay(einsum(J_regressor, verts[[0]], "j v, l v i -> l j i"), inverse=True)
        verts = apply_T_on_points(verts, T_ay2ayfz)
        return verts

    verts_glob = move_to_start_point_face_z(pred_ay_verts)
    joints_glob = einsum(J_regressor, verts_glob, "j v, l v i -> l j i")  # (L, J, 3)
    global_R, global_T, global_lights = get_global_cameras_static(
        verts_glob.cpu(),
        beta=2.0,
        cam_height_degree=20,
        target_center_height=1.0,
    )

    # -- rendering code -- #
    video_path = cfg.video_path
    length, width, height = get_video_lwh(video_path)
    _, _, K = create_camera_sensor(width, height, 24)  # render as 24mm lens

    # renderer
    renderer = Renderer(width, height, device="cuda", faces=faces_smpl, K=K)
    # renderer = Renderer(width, height, device="cuda", faces=faces_smpl, K=K, bin_size=0)

    # -- render mesh -- #
    scale, cx, cz = get_ground_params_from_points(joints_glob[:, 0], verts_glob)
    renderer.set_ground(scale * 1.5, cx, cz)
    color = torch.ones(3).float().cuda() * 0.8

    render_length = length if not debug_cam else 8
    writer = get_writer(global_video_path, fps=30, crf=CRF)
    for i in tqdm(range(render_length), desc=f"Rendering Global"):
        cameras = renderer.create_camera(global_R[i], global_T[i])
        img = renderer.render_with_ground(verts_glob[[i]], color[None], cameras, global_lights)
        writer.write_frame(img)
    writer.close()


def savez(npz, new_data, mode: Literal['w', 'a'] = 'a'):
    if mode == 'a' and Path(npz).exists():
        new_data = {**np.load(npz, allow_pickle=True), **new_data}
    np.savez_compressed(npz, **new_data)


def torch_to_numpy(
    pred: dict,
    file: Union[Path, str] = 'gvhmr.npz',
    person=0,
):
    """
    Convert `'pred'` torch tensors (.pt) to numpy (.npz) and save to out_path.
    """
    pred_np = {}
    keyname = {
        'smpl_params_global': f'smplx;gvhmr;{person};global;',
        'smpl_params_incam': f'smplx;gvhmr;{person};incam;',
    }
    keyname_deep = {
        'body_pose': 'pose;',
        'global_orient': 'rotate;',
        'transl': 'trans;',
        'betas': 'shape',
    }

    for K, K_ in keyname.items():
        for k, k_ in keyname_deep.items():
            pred_np[K_ + k_] = pred[K][k].cpu().numpy()

    savez(file, pred_np)
    # with open(out_path, 'wb') as handle:
    #     pickle.dump(pred_np, handle, protocol=pickle.HIGHEST_PROTOCOL)


def find_camera_extrinsics(verts_world, verts_camera):
    """
    Find camera extrinsics (R, T) given vertices in world and camera coordinate systems.

    Args:
        verts_world: (N, 3) Vertices in world coordinates.
        verts_camera: (N, 3) Vertices in camera coordinates.

    Returns:
        R: (3, 3) Rotation matrix.
        T: (3,) Translation vector.
    """
    # Compute centroids
    centroid_world = verts_world.mean(dim=0)
    centroid_camera = verts_camera.mean(dim=0)

    # Center the points
    centered_verts_world = verts_world - centroid_world
    centered_verts_camera = verts_camera - centroid_camera

    # Compute the cross-covariance matrix
    H = centered_verts_camera.T @ centered_verts_world

    # Perform SVD
    U, _, Vt = torch.linalg.svd(H)

    # Compute rotation matrix
    R = U @ Vt
    # Ensure R is a proper rotation matrix
    if torch.det(R) < 0:
        U[:, -1] *= -1  # Adjust U if determinant is negative
        R = U @ Vt

    # Compute translation vector
    T = centroid_camera - R @ centroid_world

    return R, T


def per_person(cfg):
    """
    run and save `.pt` results to disk, for each person.

    Returns:
        pred: dict, torch.tensor
    """
    paths = cfg.paths
    pred = {}
    hmr4d_results = paths.hmr4d_results
    if not Path(hmr4d_results).exists():
        # ===== Preprocess and save to disk ===== #
        run_preprocess(cfg)
        data = load_data_dict(cfg)

        # ===== HMR4D ===== #
        Log.info("[HMR4D] Predicting")
        model: DemoPL = hydra.utils.instantiate(cfg.model, _recursive_=False)
        model.load_pretrained_model(cfg.ckpt_path)
        model = model.eval().cuda()
        tic = Log.sync_time()
        pred = model.predict(data, static_cam=cfg.static_cam)
        pred = detach_to_cpu(pred)
        data_time = data["length"] / 30
        Log.info(f"[HMR4D] Elapsed: {Log.sync_time() - tic:.2f}s for data-length={data_time:.1f}s")
        torch.save(pred, hmr4d_results)
    else:
        pred = torch.load(hmr4d_results)

    # ===== Check camera extrinsics ===== #
    # R, T = find_camera_extrinsics(verts_world, verts_camera)
    # verts_camera_pred = (verts_world @ R.T) + T
    # print(torch.allclose(verts_camera_pred, verts_camera, atol=1e-6))  # Should return True

    # ===== Render ===== #
    if cfg.render:
        render_incam(cfg)
        render_global(cfg)
        if not Path(paths.incam_global_horiz_video).exists():
            Log.info("[Merge Videos]")
            merge_videos_horizontal([paths.incam_video, paths.global_video], paths.incam_global_horiz_video)
    free_ram()
    return pred


def main(Persons: Union[Sequence[int], Set[int], None] = None):
    cfg = parse_args_to_cfg()
    # Log.info(f"[GPU]: {torch.cuda.get_device_name()}")
    Log.info(f'[GPU]: {torch.cuda.get_device_properties("cuda")}')

    run_preprocess(cfg)
    # Log.info(f'cfg.persons = {cfg.persons}, type={type(cfg.persons)}')
    if not Persons:
        Persons = set(cfg.persons)
        # if still None
        if not Persons:
            Log.info(f"Persons = {Persons}")
            if person_count is None:
                load_yolo_track(cfg)
            if person_count is not None:
                Persons = range(0, person_count)
            else:
                Persons = [0]
    for p in Persons:
        cfg.person = p
        Log.info(f"[Person {p}] from {Persons}")
        pred = per_person(cfg)
        # === pkl === #
        out_path = Path(cfg.output_dir).joinpath(f"mocap_gvhmr_{cfg.video_name}.npz")
        torch_to_numpy(pred, out_path, person=p)


if __name__ == "__main__":
    main()
