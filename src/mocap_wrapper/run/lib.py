import os
import sys
import toml
import argparse
import numpy as np
from typing_extensions import deprecated
from platformdirs import user_config_path
from types import ModuleType
from typing import Literal, Sequence, TypeVar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # relative import
try:
    from ..logger import getLogger, cleanup
except ImportError:
    from logger import getLogger, cleanup   # type: ignore
cleanup()
MAPPING = {
    'gvhmr': 'GVHMR',
}
TYPE_RANGE = tuple[int, int]
T = TypeVar('T')
TN = TypeVar('NT', 'np.ndarray', 'torch.Tensor')    # type: ignore
Log = getLogger(__name__)


def chdir_gitRepo(mod: Literal['gvhmr']):
    config_path = user_config_path(appname='mocap_wrapper', ensure_exists=True).joinpath('config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        dst = os.path.join(config['search_dir'], MAPPING[mod])
        sys.path.append(dst)
        os.chdir(dst)
    else:
        raise FileNotFoundError(f'config.toml not found in {config_path}')


def continuous(List: Sequence[int]) -> list[tuple[int, int]]:
    """
    Detect continuous parts in a sorted list.

    Args:
        List: A sorted list of integers, e.g., [0, 1, 2, 10, 11]

    Returns:
        list(tuple): Each tuple represents a continuous interval, e.g., [(0, 2), (10, 11)]
    """
    if not List:
        return []
    result = []
    start = List[0]
    end = start
    for num in List[1:]:
        if num == end + 1:
            end = num
        else:
            result.append((start, end))
            start = num
            end = num
    result.append((start, end))
    return result


def invert_ranges(ranges: Sequence[tuple], total_range: tuple) -> list[tuple]:
    """
    Invert the given ranges within the total_range.

    Args:
        ranges: A sequence of ranges to be inverted.
        total_range: The total range within which the inversion is performed.

    Returns:
        list(tuple): The inverted ranges.
    """
    total_start, total_end = total_range
    valid_ranges = []
    # Truncate ranges to fit within total_range and collect valid ones
    for r in ranges:
        start = max(r[0], total_start)
        end = min(r[1], total_end)
        if start < end:
            valid_ranges.append((start, end))

    # Merge overlapping or adjacent ranges
    if not valid_ranges:
        return [(total_start, total_end)] if total_start < total_end else []

    sorted_ranges = sorted(valid_ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]
    for current in sorted_ranges[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)

    # Generate inverted ranges
    inverted = []
    prev_end = total_start
    for interval in merged:
        current_start = interval[0]
        if prev_end < current_start:
            inverted.append((prev_end, current_start))
        prev_end = max(prev_end, interval[1])
    if prev_end < total_end:
        inverted.append((prev_end, total_end))

    return inverted


def squeeze(v: np.ndarray, axis=0, key=''):
    if not isinstance(v, np.ndarray):
        return v
    shape_old = v.shape
    while len(v.shape) > axis and v.shape[axis] == 1:  # TODO: maybe buggy
        v = np.squeeze(v, axis=axis)
    Log.debug(f"🧽 key squeezed: {key}, {v.shape} ← {shape_old}") if shape_old != v.shape else None
    return v


def _get_mod(mod1: ModuleType | str):
    if isinstance(mod1, str):
        _mod1 = sys.modules.get(mod1, None)
    else:
        _mod1 = mod1
    return _mod1


def Lib(arr, mod1: ModuleType | str = np, mod2: ModuleType | str = 'torch', ret_1_if=np.ndarray):
    """usage:
    ```python
    lib = Lib(arr)
    is_torch = lib.__name__ == 'torch'
    ```
    """
    _mod1 = _get_mod(mod1)
    _mod2 = _get_mod(mod2)
    if _mod1 and _mod2:
        mod = _mod1 if isinstance(arr, ret_1_if) else _mod2
    elif _mod1:
        mod = _mod1
    elif _mod2:
        mod = _mod2
    else:
        raise ImportError("Both libraries are not available.")
    Log.debug(f"🔍 {mod}: {mod.__name__}, {dir(arr)}")
    return mod


def Norm(arr: TN, dim: int = -1, keepdim: bool = True) -> TN:
    """计算范数，支持批量输入"""
    lib = Lib(arr)
    is_torch = lib.__name__ == 'torch'
    if is_torch:
        return lib.norm(arr, dim=dim, keepdim=keepdim)
    else:
        return lib.linalg.norm(arr, axis=dim, keepdims=keepdim)


def skew_symmetric(v: TN) -> TN:
    """生成反对称矩阵，支持批量输入"""
    lib = Lib(v)
    is_torch = lib.__name__ == 'torch'
    axis = Axis(is_torch)
    axis_1 = {axis: -1}
    # 创建各分量
    zeros = lib.zeros_like(v[..., 0])  # 形状 (...)
    row0 = lib.stack([zeros, -v[..., 2], v[..., 1]], **axis_1)  # (...,3)
    row1 = lib.stack([v[..., 2], zeros, -v[..., 0]], **axis_1)
    row2 = lib.stack([-v[..., 1], v[..., 0], zeros], **axis_1)
    # 堆叠为矩阵
    if is_torch:
        return lib.stack([row0, row1, row2], dim=-2)
    else:
        return lib.stack([row0, row1, row2], axis=-2)  # (...,3,3)


def Rodrigues(rot_vec3: TN) -> TN:
    """
    支持批量处理的罗德里格斯公式

    Parameters
    ----------
    rotvec : np.ndarray
        3D rotation vector

    Returns
    -------
    np.ndarray
        3x3 rotation matrix

    _R: np.ndarray = np.eye(3) + sin * K + (1 - cos) * K @ K  # 原式
    choose (3,1) instead 3:    3 is vec, k.T == k;    (3,1) is matrix, k.T != k
    """
    if rot_vec3.shape[-1] == 4:
        return rot_vec3
    assert rot_vec3.shape[-1] == 3, f"Last dimension must be 3, but got {rot_vec3.shape}"
    lib = Lib(rot_vec3)
    is_torch = lib.__name__ == 'torch'

    # 计算旋转角度
    theta = Norm(rot_vec3, dim=-1, keepdim=True)  # (...,1)

    EPSILON = 1e-8
    mask = theta < EPSILON

    # 处理小角度情况
    K_small = skew_symmetric(rot_vec3)
    eye = lib.eye(3, dtype=rot_vec3.dtype)
    if is_torch:
        eye = eye.to(rot_vec3.device)
    R_small = eye + K_small  # 广播加法

    # 处理一般情况
    safe_theta = lib.where(mask, EPSILON * lib.ones_like(theta), theta)  # 避免除零
    k = rot_vec3 / safe_theta  # 单位向量

    K = skew_symmetric(k)
    k = k[..., None]  # 添加最后维度 (...,3,1)
    kkt = lib.matmul(k, lib.swapaxes(k, -1, -2))  # (...,3,3)

    cos_t = lib.cos(theta)[..., None]  # (...,1,1)
    sin_t = lib.sin(theta)[..., None]

    R_full = cos_t * eye + sin_t * K + (1 - cos_t) * kkt

    # 合并结果
    if is_torch:
        mask = mask.view(*mask.shape[:-1], 1, 1)
    else:
        mask = mask[..., None]

    ret = lib.where(mask, R_small, R_full)
    return ret


def RotMat_to_quat(R: TN) -> TN:
    """将3x3旋转矩阵转换为单位四元数 [w, x, y, z]，支持批量和PyTorch/NumPy"""
    if R.shape[-1] == 4:
        return R
    assert R.shape[-2:] == (3, 3), f"输入R的末两维必须为3x3，当前为{R.shape}"
    lib = Lib(R)  # 自动检测模块
    is_torch = lib.__name__ == 'torch'
    EPSILON = 1e-12  # 数值稳定系数

    # 计算迹，形状为(...)
    trace = lib.einsum('...ii->...', R)

    # 计算四个分量的平方（带数值稳定处理）
    q_sq = lib.stack([
        (trace + 1) / 4,
        (1 + 2 * R[..., 0, 0] - trace) / 4,
        (1 + 2 * R[..., 1, 1] - trace) / 4,
        (1 + 2 * R[..., 2, 2] - trace) / 4,
    ], axis=-1)

    other = 0.0
    if is_torch:
        other = lib.zeros_like(q_sq)
    q_sq = lib.maximum(q_sq, other)  # 确保平方值非负

    # 找到最大分量的索引，形状(...)
    i = lib.argmax(q_sq, axis=-1)

    # 计算分母（带数值稳定处理）
    denoms = 4 * lib.sqrt(q_sq + EPSILON)  # 添加极小值防止sqrt(0)

    # 构造每个case的四元数分量
    cases = []
    for i_case in range(4):
        denom = denoms[..., i_case]  # 当前case的分母
        if i_case == 0:
            w = lib.sqrt(q_sq[..., 0] + EPSILON)  # 数值稳定
            x = (R[..., 2, 1] - R[..., 1, 2]) / denom
            y = (R[..., 0, 2] - R[..., 2, 0]) / denom
            z = (R[..., 1, 0] - R[..., 0, 1]) / denom
        elif i_case == 1:
            x = lib.sqrt(q_sq[..., 1] + EPSILON)
            w = (R[..., 2, 1] - R[..., 1, 2]) / denom
            y = (R[..., 0, 1] + R[..., 1, 0]) / denom
            z = (R[..., 0, 2] + R[..., 2, 0]) / denom
        elif i_case == 2:
            y = lib.sqrt(q_sq[..., 2] + EPSILON)
            w = (R[..., 0, 2] - R[..., 2, 0]) / denom
            x = (R[..., 0, 1] + R[..., 1, 0]) / denom
            z = (R[..., 1, 2] + R[..., 2, 1]) / denom
        else:  # i_case == 3
            z = lib.sqrt(q_sq[..., 3] + EPSILON)
            w = (R[..., 1, 0] - R[..., 0, 1]) / denom
            x = (R[..., 0, 2] + R[..., 2, 0]) / denom
            y = (R[..., 1, 2] + R[..., 2, 1]) / denom

        case = lib.stack([w, x, y, z], axis=-1)
        cases.append(case)

    # 合并所有情况并进行索引选择
    cases = lib.stack(cases, axis=0)
    if is_torch:
        index = i.reshape(1, *i.shape, 1).expand(1, *i.shape, 4)
        q = lib.gather(cases, dim=0, index=index).squeeze(0)
    else:
        # 构造NumPy兼容的索引
        index = i.reshape(1, *i.shape, 1)  # 添加新轴以对齐批量维度
        index = np.broadcast_to(index, (1,) + i.shape + (4,))  # 扩展至四元数维度
        q = np.take_along_axis(cases, index, axis=0).squeeze(0)  # 选择并压缩维度

    # 归一化处理（带数值稳定）
    norm = Norm(q, dim=-1, keepdim=True)
    ret = q / (norm + EPSILON)  # 防止除零
    return ret


def RotMat_to_new(R: TN, out=4) -> TN:
    """将3x3旋转矩阵转换为单位四元数 [w, x, y, z] 或欧拉角(xyz顺序)，支持批量和PyTorch/NumPy"""
    if R.shape[-1] == out:
        return R
    assert R.shape[-2:] == (3, 3), f"输入R的末两维必须为3x3，当前为{R.shape}"
    lib = Lib(R)  # 自动检测模块
    is_torch = lib.__name__ == 'torch'
    EPSILON = 1e-12  # 数值稳定系数

    if out == 4:
        # 计算迹，形状为(...)
        trace = lib.einsum('...ii->...', R)

        # 计算四个分量的平方（带数值稳定处理）
        q_sq = lib.stack([
            (trace + 1) / 4,
            (1 + 2 * R[..., 0, 0] - trace) / 4,
            (1 + 2 * R[..., 1, 1] - trace) / 4,
            (1 + 2 * R[..., 2, 2] - trace) / 4,
        ], axis=-1)

        other = 0.0
        if is_torch:
            other = lib.zeros_like(q_sq)
        q_sq = lib.maximum(q_sq, other)  # 确保平方值非负

        # 找到最大分量的索引，形状(...)
        i = lib.argmax(q_sq, axis=-1)

        # 计算分母（带数值稳定处理）
        denoms = 4 * lib.sqrt(q_sq + EPSILON)  # 添加极小值防止sqrt(0)

        # 构造每个case的四元数分量
        cases = []
        for i_case in range(4):
            denom = denoms[..., i_case]  # 当前case的分母
            if i_case == 0:
                w = lib.sqrt(q_sq[..., 0] + EPSILON)  # 数值稳定
                x = (R[..., 2, 1] - R[..., 1, 2]) / denom
                y = (R[..., 0, 2] - R[..., 2, 0]) / denom
                z = (R[..., 1, 0] - R[..., 0, 1]) / denom
            elif i_case == 1:
                x = lib.sqrt(q_sq[..., 1] + EPSILON)
                w = (R[..., 2, 1] - R[..., 1, 2]) / denom
                y = (R[..., 0, 1] + R[..., 1, 0]) / denom
                z = (R[..., 0, 2] + R[..., 2, 0]) / denom
            elif i_case == 2:
                y = lib.sqrt(q_sq[..., 2] + EPSILON)
                w = (R[..., 0, 2] - R[..., 2, 0]) / denom
                x = (R[..., 0, 1] + R[..., 1, 0]) / denom
                z = (R[..., 1, 2] + R[..., 2, 1]) / denom
            else:  # i_case == 3
                z = lib.sqrt(q_sq[..., 3] + EPSILON)
                w = (R[..., 1, 0] - R[..., 0, 1]) / denom
                x = (R[..., 0, 2] + R[..., 2, 0]) / denom
                y = (R[..., 1, 2] + R[..., 2, 1]) / denom

            case = lib.stack([w, x, y, z], axis=-1)
            cases.append(case)

        # 合并所有情况并进行索引选择
        cases = lib.stack(cases, axis=0)
        if is_torch:
            index = i.reshape(1, *i.shape, 1).expand(1, *i.shape, 4)
            q = lib.gather(cases, dim=0, index=index).squeeze(0)
        else:
            # 构造NumPy兼容的索引
            index = i.reshape(1, *i.shape, 1)  # 添加新轴以对齐批量维度
            index = np.broadcast_to(index, (1,) + i.shape + (4,))  # 扩展至四元数维度
            q = np.take_along_axis(cases, index, axis=0).squeeze(0)  # 选择并压缩维度

        # 归一化处理（带数值稳定）
        norm = Norm(q, dim=-1, keepdim=True)
        ret = q / (norm + EPSILON)  # 防止除零
        return ret
    elif out == 3:
        if is_torch:
            sy = torch.sqrt(R[..., 0, 0] * R[..., 0, 0] + R[..., 1, 0] * R[..., 1, 0])
            singular = sy < 1e-6
            if singular.any():
                x = torch.atan2(-R[..., 1, 2], R[..., 1, 1])
                y = torch.atan2(-R[..., 2, 0], sy)
                z = torch.zeros_like(x)
            else:
                x = torch.atan2(R[..., 2, 1], R[..., 2, 2])
                y = torch.atan2(-R[..., 2, 0], sy)
                z = torch.atan2(R[..., 1, 0], R[..., 0, 0])
            return torch.stack([x, y, z], dim=-1)
        else:
            sy = np.sqrt(R[..., 0, 0] * R[..., 0, 0] + R[..., 1, 0] * R[..., 1, 0])
            singular = sy < 1e-6
            if np.any(singular):
                x = np.arctan2(-R[..., 1, 2], R[..., 1, 1])
                y = np.arctan2(-R[..., 2, 0], sy)
                z = np.zeros_like(x)
            else:
                x = np.arctan2(R[..., 2, 1], R[..., 2, 2])
                y = np.arctan2(-R[..., 2, 0], sy)
                z = np.arctan2(R[..., 1, 0], R[..., 0, 0])
            return np.stack([x, y, z], axis=-1)
    else:
        raise ValueError("out参数只能为3或4")


def quat_rotAxis(arr: TN) -> TN: return RotMat_to_quat(Rodrigues(arr))
def Axis(is_torch=False): return 'dim' if is_torch else 'axis'


@deprecated('use `quat_rotAxis`')
def quat(xyz: TN) -> TN:
    """euler to quat
    Args:
        arr (TN): 输入张量/数组，shape为(...,3)，对应[roll, pitch, yaw]（弧度）
    Returns:
        quat: normalized [w,x,y,z], shape==(...,4)
    """
    if xyz.shape[-1] == 4:
        return xyz
    assert xyz.shape[-1] == 3, f"Last dimension should be 3, but found {xyz.shape}"
    lib = Lib(xyz)  # 自动检测库类型
    is_torch = lib.__name__ == 'torch'

    # 计算半角三角函数（支持广播）
    half_angles = 0.5 * xyz
    cos_half = lib.cos(half_angles)  # shape (...,3)
    sin_half = lib.sin(half_angles)

    # 分库处理维度解包
    if is_torch:
        cr, cp, cy = cos_half.unbind(dim=-1)
        sr, sp, sy = sin_half.unbind(dim=-1)
    else:  # NumPy处理
        cr, cp, cy = cos_half[..., 0], cos_half[..., 1], cos_half[..., 2]
        sr, sp, sy = sin_half[..., 0], sin_half[..., 1], sin_half[..., 2]

    # 并行计算四元数分量（保持维度）
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    # 堆叠并归一化
    _quat = lib.stack([w, x, y, z], **{Axis(is_torch): -1})
    return _quat / Norm(_quat, dim=-1, keepdim=True)


def euler(wxyz: TN) -> TN:
    """union quat to euler
    Args:
        quat (TN): [w,x,y,z], shape==(...,4)
    Returns:
        euler: [roll_x, pitch_y, yaw_z] in arc system, shape==(...,3)
    """
    if wxyz.shape[-1] == 3:
        return wxyz
    assert wxyz.shape[-1] == 4, f"Last dimension should be 4, but found {wxyz.shape}"
    lib = Lib(wxyz)  # 自动检测库类型
    is_torch = lib.__name__ == 'torch'
    EPSILON = 1e-12  # 数值稳定系数

    # 归一化四元数（防止输入未归一化）
    wxyz = wxyz / Norm(wxyz, dim=-1, keepdim=True)  # type: ignore

    # 解包四元数分量（支持广播）
    w, x, y, z = wxyz[..., 0], wxyz[..., 1], wxyz[..., 2], wxyz[..., 3]

    # 计算roll (x轴旋转)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x**2 + y**2)
    roll = lib.arctan2(sinr_cosp, cosr_cosp + EPSILON)  # 防止除零

    # 计算pitch (y轴旋转)
    # 原始公式存在数值问题，改用更稳定的版本
    sinp = 2 * (w * y - z * x)
    pitch = lib.arcsin(sinp.clip(-1.0, 1.0))  # 限制在有效范围内

    # 计算yaw (z轴旋转)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y**2 + z**2)
    yaw = lib.arctan2(siny_cosp, cosy_cosp + EPSILON)

    # 堆叠结果
    _euler = lib.stack([roll, pitch, yaw], **{Axis(is_torch): -1})
    return _euler


def compute_global_rotation(pose_axis_anges, joint_idx):
    """
    calculating joints' global rotation
    Args:
        pose_axis_anges (np.array): SMPLX's local pose (22,3)
    Returns:
        np.array: (3, 3)
    """
    global_rotation = np.eye(3)
    parents = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19]
    while joint_idx != -1:
        joint_rotation = Rodrigues(pose_axis_anges[joint_idx])
        global_rotation = joint_rotation @ global_rotation
        joint_idx = parents[joint_idx]
    return global_rotation


def mano_to_smplx(smplx_body_gvhmr, mano_hand_hamer):
    """https://github.com/VincentHu19/Mano2Smpl-X/blob/main/mano2smplx.py"""
    M = np.diag([-1, 1, 1])  # Preparing for the left hand switch

    lib = Lib(smplx_body_gvhmr["global_orient"])
    # Assuming that your data are stored in gvhmr_smplx_params and hamer_mano_params
    full_body_pose = lib.concatenate((smplx_body_gvhmr["global_orient"], smplx_body_gvhmr["body_pose"].reshape(21, 3)), dim=0)     # gvhmr_smplx_params["global_orient"]: (3, 3)
    left_elbow_global_rot = compute_global_rotation(full_body_pose, 18)  # left elbow IDX: 18
    right_elbow_global_rot = compute_global_rotation(full_body_pose, 19)  # left elbow IDX: 19

    left_wrist_global_rot = mano_hand_hamer["global_orient"][0].cpu().numpy()  # hamer_mano_params["global_orient"]: (2, 3, 3)
    left_wrist_global_rot = M @ left_wrist_global_rot @ M  # mirror switch
    left_wrist_pose = np.linalg.inv(left_elbow_global_rot) @ left_wrist_global_rot

    right_wrist_global_rot = mano_hand_hamer["global_orient"][1].cpu().numpy()
    right_wrist_pose = np.linalg.inv(right_elbow_global_rot) @ right_wrist_global_rot

    left_wrist_pose_vec = euler(RotMat_to_quat(left_wrist_pose))
    right_wrist_pose_vec = euler(RotMat_to_quat(right_wrist_pose))

    left_hand_pose = np.ones(45)
    right_hand_pose = np.ones(45)
    for i in range(15):
        left_finger_pose = M @ mano_hand_hamer["hand_pose"][0][i].cpu().numpy() @ M  # hamer_mano_params["hand_pose"]: (2, 15, 3, 3)
        left_finger_pose_vec = euler(RotMat_to_quat(left_finger_pose))
        left_hand_pose[i * 3: i * 3 + 3] = left_finger_pose_vec

        right_finger_pose = mano_hand_hamer["hand_pose"][1][i].cpu().numpy()
        right_finger_pose_vec = euler(RotMat_to_quat(right_finger_pose))
        right_hand_pose[i * 3: i * 3 + 3] = right_finger_pose_vec

    smplx_body_gvhmr["body_pose"][57: 60] = left_wrist_pose_vec
    smplx_body_gvhmr["body_pose"][60: 63] = right_wrist_pose_vec
    smplx_body_gvhmr["left_hand_pose"] = left_hand_pose
    smplx_body_gvhmr["right_hand_pose"] = right_hand_pose


class ArgParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        super().print_help(file)
        exit(1)


if __name__ == '__main__':
    arr = np.array([[1, 1, 1], [1, 0, 0]])
    _arr = quat(arr)
    print(_arr.shape, _arr)
    _arr = euler(_arr)
    print(_arr.shape, _arr)
    _arr = Rodrigues(arr)
    print(_arr.shape, _arr)
    _arr = RotMat_to_quat(_arr)
    print(_arr.shape, _arr)
