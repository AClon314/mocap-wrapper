#!/usr/bin/env -S pixi -e mocap -- python
# -*- coding: utf-8 -*-
# @Time    : 2024/10/14
# @Author  : wenshao(original), AClon314(modified)
# @Project : WiLoR-mini
# @FileName: test_wilor_pipeline.py
"""
https://github.com/warmshao/WiLoR-mini/blob/main/tests/test_pipelines.py
"""

"""
you need to install trimesh and pyrender if you want to render mesh
pip install trimesh
pip install pyrender
"""
IS_RENDER = IS_RAW = IS_EXPORT_OBJ = False
OUTDIR = 'output'
LIGHT_PURPLE = (0.25098039, 0.274117647, 0.65882353)
import os
import argparse
import numpy as np
from typing import Literal, Sequence, get_args
from lib import quat_rotAxis, savez, squeeze, VIDEO_EXT
# from rich.progress import (
#     Progress, TextColumn, BarColumn, TaskProgressColumn, MofNCompleteColumn, TimeElapsedColumn, TimeRemainingColumn)
from sys import platform
is_win = platform == "win32"
is_linux = platform == "linux"
if not is_win:
    os.environ['PYOPENGL_PLATFORM'] = 'egl'  # linux fix
_PREFIX = '_out_'
_TYPE_WILOR = Literal['bbox', 'betas', 'global_orient', 'hand_pose', 'pred_cam', 'pred_cam_t_full', 'pred_keypoints_2d', 'pred_keypoints_3d', 'pred_vertices', 'scaled_focal_length', ]
_WILOR_KEYS: tuple[str] = get_args(_TYPE_WILOR)
def no_ext_filename(path) -> str: return os.path.splitext(os.path.basename(path))[0]


def create_raymond_lights():
    """
    Return raymond light nodes for the scene.
    """
    thetas = np.pi * np.array([1.0 / 6.0, 1.0 / 6.0, 1.0 / 6.0])
    phis = np.pi * np.array([0.0, 2.0 / 3.0, 4.0 / 3.0])

    nodes = []

    for phi, theta in zip(phis, thetas):
        xp = np.sin(theta) * np.cos(phi)
        yp = np.sin(theta) * np.sin(phi)
        zp = np.cos(theta)

        z = np.array([xp, yp, zp])
        z = z / np.linalg.norm(z)
        x = np.array([-z[1], z[0], 0.0])
        if np.linalg.norm(x) == 0:
            x = np.array([1.0, 0.0, 0.0])
        x = x / np.linalg.norm(x)
        y = np.cross(z, x)

        matrix = np.eye(4)
        matrix[:3, :3] = np.c_[x, y, z]
        nodes.append(pyrender.Node(
            light=pyrender.DirectionalLight(color=np.ones(3), intensity=1.0),
            matrix=matrix
        ))

    return nodes


def get_light_poses(n_lights: float = 5, elevation=np.pi / 3, dist: float = 12):
    # get lights in a circle around origin at elevation
    thetas = elevation * np.ones(n_lights)  # type: ignore
    phis = 2 * np.pi * np.arange(n_lights) / n_lights
    poses = []
    trans = make_translation(torch.tensor([0, 0, dist]))
    for phi, theta in zip(phis, thetas):
        rot = make_rotation(rx=-theta, ry=phi, order="xyz")
        poses.append((rot @ trans).numpy())
    return poses


def make_translation(t):
    return make_4x4_pose(torch.eye(3), t)


def make_rotation(rx=0, ry=0, rz=0, order="xyz"):
    Rx = rotx(rx)
    Ry = roty(ry)
    Rz = rotz(rz)
    if order == "xyz":
        R = Rz @ Ry @ Rx
    elif order == "xzy":
        R = Ry @ Rz @ Rx
    elif order == "yxz":
        R = Rz @ Rx @ Ry
    elif order == "yzx":
        R = Rx @ Rz @ Ry
    elif order == "zyx":
        R = Rx @ Ry @ Rz
    elif order == "zxy":
        R = Ry @ Rx @ Rz
    return make_4x4_pose(R, torch.zeros(3))


def make_4x4_pose(R, t):
    """
    :param R (*, 3, 3)
    :param t (*, 3)
    return (*, 4, 4)
    """
    dims = R.shape[:-2]
    pose_3x4 = torch.cat([R, t.view(*dims, 3, 1)], dim=-1)
    bottom = (
        torch.tensor([0, 0, 0, 1], device=R.device)
        .reshape(*(1,) * len(dims), 1, 4)
        .expand(*dims, 1, 4)
    )
    return torch.cat([pose_3x4, bottom], dim=-2)


def rotx(theta):
    return torch.tensor(
        [
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)],
        ],
        dtype=torch.float32,
    )


def roty(theta):
    return torch.tensor(
        [
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)],
        ],
        dtype=torch.float32,
    )


def rotz(theta):
    return torch.tensor(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ],
        dtype=torch.float32,
    )


class Renderer:

    def __init__(self, faces: np.ndarray):
        """
        Wrapper around the pyrender renderer to render MANO meshes.
        Args:
            cfg (CfgNode): Model config file.
            faces (np.array): Array of shape (F, 3) containing the mesh faces.
        """

        # add faces that make the hand mesh watertight
        faces_new = np.array(
            [[92, 38, 234],
             [234, 38, 239],
             [38, 122, 239],
             [239, 122, 279],
             [122, 118, 279],
             [279, 118, 215],
             [118, 117, 215],
             [215, 117, 214],
             [117, 119, 214],
             [214, 119, 121],
             [119, 120, 121],
             [121, 120, 78],
             [120, 108, 78],
             [78, 108, 79]])
        faces = np.concatenate([faces, faces_new], axis=0)
        self.faces = faces
        self.faces_left = self.faces[:, [0, 2, 1]]

    def vertices_to_trimesh(self, vertices, camera_translation, mesh_base_color=(1.0, 1.0, 0.9),
                            rot_axis=[1, 0, 0], rot_angle=0, is_right=1):
        # material = pyrender.MetallicRoughnessMaterial(
        #     metallicFactor=0.0,
        #     alphaMode='OPAQUE',
        #     baseColorFactor=(*mesh_base_color, 1.0))
        vertex_colors = np.array([(*mesh_base_color, 1.0)] * vertices.shape[0])
        if is_right:
            faces = self.faces.copy()
        else:
            faces = self.faces_left.copy()
        mesh = trimesh.Trimesh(vertices.copy() + camera_translation, faces, vertex_colors=vertex_colors)
        # mesh = trimesh.Trimesh(vertices.copy(), self.faces.copy())

        rot = trimesh.transformations.rotation_matrix(
            np.radians(rot_angle), rot_axis)
        mesh.apply_transform(rot)

        rot = trimesh.transformations.rotation_matrix(
            np.radians(180), [1, 0, 0])
        mesh.apply_transform(rot)
        return mesh

    def render_rgba(
            self,
            vertices: np.ndarray,
            cam_t=None,
            rot=None,
            rot_axis=[1, 0, 0],
            rot_angle=0,
            camera_z=3,
            # camera_translation: np.array,
            mesh_base_color=(1.0, 1.0, 0.9),
            scene_bg_color=(0, 0, 0),
            render_res=[256, 256],
            focal_length=None,
            is_right=None,
    ):

        renderer = pyrender.OffscreenRenderer(
            viewport_width=render_res[0],
            viewport_height=render_res[1],
            point_size=1.0)
        # material = pyrender.MetallicRoughnessMaterial(
        #     metallicFactor=0.0,
        #     alphaMode='OPAQUE',
        #     baseColorFactor=(*mesh_base_color, 1.0))

        if cam_t is not None:
            camera_translation = cam_t.copy()
            camera_translation[0] *= -1.
        else:
            camera_translation = np.array([0, 0, camera_z * focal_length / render_res[1]])
        if is_right:
            mesh_base_color = mesh_base_color[::-1]
        mesh = self.vertices_to_trimesh(
            vertices, np.array([0, 0, 0]), mesh_base_color,
            rot_axis, rot_angle, is_right=is_right)
        mesh = pyrender.Mesh.from_trimesh(mesh)
        # mesh = pyrender.Mesh.from_trimesh(mesh, material=material)

        scene = pyrender.Scene(bg_color=[*scene_bg_color, 0.0], ambient_light=(0.3, 0.3, 0.3))
        scene.add(mesh, 'mesh')

        camera_pose = np.eye(4)
        camera_pose[:3, 3] = camera_translation
        camera_center = [render_res[0] / 2., render_res[1] / 2.]
        camera = pyrender.IntrinsicsCamera(
            fx=focal_length, fy=focal_length,
            cx=camera_center[0], cy=camera_center[1], zfar=1e12)

        # Create camera node and add it to pyRender scene
        camera_node = pyrender.Node(camera=camera, matrix=camera_pose)
        scene.add_node(camera_node)
        self.add_point_lighting(scene, camera_node)
        self.add_lighting(scene, camera_node)

        light_nodes = create_raymond_lights()
        for node in light_nodes:
            scene.add_node(node)

        color, rend_depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        color = color.astype(np.float32) / 255.0
        renderer.delete()

        return color

    def add_lighting(self, scene, cam_node, color=np.ones(3), intensity=1.0):
        # from phalp.visualize.py_renderer import get_light_poses
        light_poses = get_light_poses()
        light_poses.append(np.eye(4))
        cam_pose = scene.get_pose(cam_node)
        for i, pose in enumerate(light_poses):
            matrix = cam_pose @ pose
            node = pyrender.Node(
                name=f"light-{i:02d}",
                light=pyrender.DirectionalLight(color=color, intensity=intensity),
                matrix=matrix,
            )
            if scene.has_node(node):
                continue
            scene.add_node(node)

    def add_point_lighting(self, scene, cam_node, color=np.ones(3), intensity=1.0):
        # from phalp.visualize.py_renderer import get_light_poses
        light_poses = get_light_poses(dist=0.5)
        light_poses.append(np.eye(4))
        cam_pose = scene.get_pose(cam_node)
        for i, pose in enumerate(light_poses):
            matrix = cam_pose @ pose
            # node = pyrender.Node(
            #     name=f"light-{i:02d}",
            #     light=pyrender.DirectionalLight(color=color, intensity=intensity),
            #     matrix=matrix,
            # )
            node = pyrender.Node(
                name=f"plight-{i:02d}",
                light=pyrender.PointLight(color=color, intensity=intensity),
                matrix=matrix,
            )
            if scene.has_node(node):
                continue
            scene.add_node(node)


def export(
    preds: list[dict[str, np.ndarray | float | int]],
    file='mocap_wilor.npz',
):
    """
    save `.npz` to file.

    keyname = 'smplx;wilor;hand{ID};prop[0];prop[1];...;props[n]'
    """
    data = {}
    prefix = 'smplx;wilor'

    for i, hand in enumerate(preds):
        LR = 'R' if hand.pop('is_right') > 0.5 else 'L'
        begin = hand.pop('begin')
        for k, v in hand.items():
            key = ';'.join([prefix, f'hand{i}{LR}', f'{begin}', k])

            if not IS_RAW and k in ['global_orient', 'hand_pose']:
                v = quat_rotAxis(v)

            if not isinstance(v, np.ndarray):
                print(f"key cast as np.ndarray: {key}")
                v = np.array(v)
            data[key] = v

    savez(file, data)


def data_remap(From: list[dict], to: list[dict], frame=0):
    """
    remap preds data for `export()` per frame

    Args:
        From: list of dicts, each dict contains hand predictions for a frame
        to: list of dicts, each dict will be updated with the remapped data

    ```python
    to_preds: list[dict] = []
    frame_count = 0
    while cap.isOpened():
        ...
        From_pred = pipe.predict(image)
        data_remap(From_pred, to_preds, frame_count)
    export(to_preds, ...)
    ```"""
    _len = len(From)
    lens = len(to)
    print(f"⚠️ Changed: {_len} hands @ {frame=}") if _len != lens else None
    BLACKLIST = ['pred_vertices', 'scaled_focal_length']    # won't save these
    TO_I = set()
    # print(f'{frame=}{_FROM_I=}')
    for _i, _hand in enumerate(From):
        # ensure to only match with not done hands
        i_to = match_nearest_hand(_hand, to, frame=frame, done_idx=TO_I)
        if i_to is None:
            i_to = len(to)
            to.append({})
        hand = to[i_to]
        TO_I.add(i_to)
        wilor_preds: dict[str, np.ndarray] = _hand["wilor_preds"]
        wilor_preds['bbox'] = _hand['hand_bbox']
        wilor_preds = {K: np.expand_dims(squeeze(v, key=K), axis=0) for K, v in wilor_preds.items() if K not in BLACKLIST}

        print(f'{i_to is None=}\t{len(hand) == 0=}') if (i_to is None) != (len(hand) == 0) else None

        if len(hand) == 0:
            print(f"➕ hand{i_to} created @ {frame=}")
            __hand = {
                'begin': frame,
                'is_right': _hand['is_right'],
                'scaled_focal_length': _hand['wilor_preds']['scaled_focal_length'],
                **wilor_preds
            }
            to[i_to] = __hand
        else:
            if _hand['is_right'] != hand['is_right']:
                print(f"❌ hand{_i} is_right changed @ {frame=}")   # this shouldn't happen
            for K in _WILOR_KEYS:
                if K in hand.keys() and K in wilor_preds.keys():
                    hand[K] = np.concatenate((hand[K], wilor_preds[K]), axis=0)
                elif K not in BLACKLIST:
                    print(f"hand{_i} {K} not in pred @ {frame=}, {hand.keys()}")  # this shouldn't happen


def match_nearest_hand(_hand: dict, to: list[dict], frame: int, done_idx: set[int] = set(), max_error=50.0) -> int | None:
    """
    根据bbox和is_right找到最佳匹配的手部索引

    Args:
        _hand: From的当前手
        to: _hand 在 `to[frame-1]` 内查找
        frame: current frame
        done_idx: exclude these idx from `to`

    Returns:
        最佳匹配的索引，如果没有找到则返回None
    """
    _bbox = np.array(_hand['hand_bbox'])
    _is_right = _hand['is_right']
    min_distance = float('inf')
    index = None

    for i, hand in enumerate(to):
        # 跳过空预测 或 已匹配
        if len(hand) == 0 or i in done_idx:
            continue

        # 优先匹配相同的左右手标识
        if hand.get('is_right') == _is_right and 'bbox' in hand:
            bbox = hand['bbox'][max(0, min(frame, len(hand['bbox'])) - 1)]
            if bbox.shape == _bbox.shape:
                # 计算bbox中心点距离
                from_center = np.array([
                    (_bbox[0] + _bbox[2]) / 2,
                    (_bbox[1] + _bbox[3]) / 2])
                to_center = np.array([
                    (bbox[0] + bbox[2]) / 2,
                    (bbox[1] + bbox[3]) / 2])
                distance = np.linalg.norm(from_center - to_center)
                if distance < min_distance:
                    min_distance = distance
                    index = i
    print(f'{min_distance=} @ {frame=}') if min_distance > max_error else None
    return index


def Import():
    from wilor_mini.pipelines.wilor_hand_pose3d_estimation_pipeline import WiLorHandPose3dEstimationPipeline, get_logger

    def __init__patch(self, **kwargs):
        self.verbose = kwargs.get("verbose", False)
        if self.verbose:
            self.logger = get_logger(self.__class__.__name__, lv=20)
        else:
            self.logger = get_logger(self.__class__.__name__, lv=40)
        self.init_models(**kwargs)
    WiLorHandPose3dEstimationPipeline.__init__ = __init__patch
    return WiLorHandPose3dEstimationPipeline


def image_wilor(input='img.png', out_dir=OUTDIR):
    WiLorHandPose3dEstimationPipeline = Import()
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    dtype = torch.float16

    pipe = WiLorHandPose3dEstimationPipeline(device=device, dtype=dtype, verbose=False)
    image = cv2.imread(input)
    pred = pipe.predict(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    filename = no_ext_filename(input)
    os.makedirs(out_dir, exist_ok=True)
    preds = []
    data_remap(pred, preds)
    export(preds, os.path.join(out_dir, f'{filename}.mocap.npz'))
    if IS_RENDER:
        renderer = Renderer(pipe.wilor_model.mano.faces)

        render_image = image.copy()
        render_image = render_image.astype(np.float32)[:, :, ::-1] / 255.0
        pred_keypoints_2d_all = []
        for i, out in enumerate(pred):
            wilor_preds = out["wilor_preds"]
            is_right = out['is_right']
            verts = wilor_preds['pred_vertices'][0]
            cam_t = wilor_preds['pred_cam_t_full'][0]
            scaled_focal_length = wilor_preds['scaled_focal_length']
            pred_keypoints_2d = wilor_preds["pred_keypoints_2d"]
            pred_keypoints_2d_all.append(pred_keypoints_2d)
            misc_args = dict(
                mesh_base_color=LIGHT_PURPLE,
                scene_bg_color=(1, 1, 1),
                focal_length=scaled_focal_length,
            )
            export_obj(renderer, verts, cam_t, is_right,
                       os.path.join(out_dir, f'{filename}_hand{i:02d}.obj'))
            cam_view = renderer.render_rgba(
                verts, cam_t=cam_t,
                render_res=[image.shape[1], image.shape[0]],
                is_right=is_right,
                **misc_args)

            # Overlay image
            render_image = render_image[:, :, :3] * (1 - cam_view[:, :, 3:]) + cam_view[:, :, :3] * cam_view[:, :, 3:]

        render_image = (255 * render_image).astype(np.uint8)
        for pred_keypoints_2d in pred_keypoints_2d_all:
            for j in range(pred_keypoints_2d[0].shape[0]):
                color = (0, 0, 255)
                radius = 3
                x, y = pred_keypoints_2d[0][j]
                cv2.circle(render_image, (int(x), int(y)), radius, color, -1)
        cv2.imwrite(os.path.join(out_dir, _PREFIX + filename + '.webp'), render_image)


def export_obj(renderer, verts, cam_t, is_right, out='{filename}_hand{idx:02d}.obj'):
    tmesh = renderer.vertices_to_trimesh(
        verts, cam_t.copy(), LIGHT_PURPLE, is_right=is_right)
    tmesh.export(out)


def video_wilor(input='video.mp4', out_dir=OUTDIR, progress: None = None):
    WiLorHandPose3dEstimationPipeline = Import()
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    dtype = torch.float16

    pipe = WiLorHandPose3dEstimationPipeline(device=device, dtype=dtype)
    os.makedirs(out_dir, exist_ok=True)
    renderer = Renderer(pipe.wilor_model.mano.faces)

    # Open the video file
    cap = cv2.VideoCapture(input)

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    filename = no_ext_filename(input)
    file = filename + '.mp4'
    task = progress.add_task(
        f"👋←📹 {file}", total=total) if progress else None

    # Create VideoWriter object
    output_path = os.path.join(out_dir, _PREFIX + file)  # tmp
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type:ignore
    vout = cv2.VideoWriter(output_path, fourcc, fps, (width, height)) if IS_RENDER else None

    if IS_EXPORT_OBJ:
        output_path_obj = os.path.join(out_dir, 'obj')
        os.makedirs(output_path_obj, exist_ok=True)
    else:
        output_path_obj = None

    preds: list[dict] = []  # hands, frames
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        _pred = pipe.predict(image)  # hands per frame
        # Convert frame to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        data_remap(_pred, preds, frame_count)

        if output_path_obj:
            for i, out in enumerate(_pred):
                wilor_preds = out["wilor_preds"]
                is_right = out['is_right']
                verts = wilor_preds['pred_vertices'][0]
                cam_t = wilor_preds['pred_cam_t_full'][0]
                export_obj(renderer, verts, cam_t, is_right,
                           os.path.join(output_path_obj, f'{filename}_hand{i:02d}_{frame_count}.obj'))

        if IS_RENDER:
            render_image = image.copy()
            render_image = render_image.astype(np.float32)[:, :, ::-1] / 255.0

            for i, out in enumerate(_pred):
                wilor_preds = out["wilor_preds"]
                is_right = out['is_right']
                verts = wilor_preds['pred_vertices'][0]
                cam_t = wilor_preds['pred_cam_t_full'][0]
                scaled_focal_length = wilor_preds['scaled_focal_length']

                misc_args = dict(
                    mesh_base_color=LIGHT_PURPLE,
                    scene_bg_color=(1, 1, 1),
                    focal_length=scaled_focal_length,
                )
                cam_view = renderer.render_rgba(
                    verts, cam_t=cam_t,
                    render_res=[image.shape[1], image.shape[0]],
                    is_right=is_right,
                    **misc_args)

                # Overlay image
                render_image = render_image[:, :, :3] * (1 - cam_view[:, :, 3:]) + cam_view[:, :, :3] * cam_view[:, :, 3:]

            render_image = (255 * render_image).astype(np.uint8)

            # Write the frame to the output video
            vout.write(render_image)

        frame_count += 1
        progress.update(task, completed=frame_count) if progress and not task is None else None

    # Release everything
    cap.release()
    vout.release() if vout else None
    cv2.destroyAllWindows()

    export(preds, os.path.join(out_dir, f'{filename}.mocap.npz'))


def argParse():
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--input', metavar='in.mp4')
    arg.add_argument('-o', '--outdir', metavar=OUTDIR, default=OUTDIR)
    arg.add_argument('--raw', action='store_true', help='raw data, NO axis angle to quaternion')
    arg.add_argument('--render', action='store_true', help='render hands mesh to video')
    arg.add_argument('--obj', action='store_true', help='export hands mesh to .obj')
    args, _args = arg.parse_known_args()
    if args.render:
        global IS_RENDER
        IS_RENDER = True
    if args.obj:
        global IS_EXPORT_OBJ
        IS_EXPORT_OBJ = True
    if args.raw:
        global IS_RAW
        IS_RAW = True
    if not args.input:
        arg.print_help()
        exit(1)
    return args, _args, arg


def wilor(args: argparse.Namespace, arg: argparse.ArgumentParser):
    if args.input:
        outdir = os.path.join(args.outdir, no_ext_filename(args.input))
        with Progress(
            TextColumn("[bold red]{task.description}"),
            BarColumn(),
            TaskProgressColumn(show_speed=True),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as p:
            if args.input.split('.')[-1].lower() not in VIDEO_EXT:
                image_wilor(input=args.input, out_dir=outdir)
            else:
                video_wilor(input=args.input, out_dir=outdir, progress=p)
    else:
        arg.print_help()


if __name__ == '__main__':
    args, _, arg = argParse()
import cv2
import torch
import pyrender
import trimesh
if __name__ == '__main__':
    wilor(args, arg)
