<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" integrity="sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==" crossorigin="anonymous" referrerpolicy="no-referrer" />

# mocap-wrapper
Addon: [mocap_importer](https://github.com/AClon314/mocap_importer_blender)

A bunch of python scripts that wrap around various mocap libraries to provide a unified interface.
Only tested on Linux. Not stable yet.

## solutions
### software:OpenSource

<table>
  <tr>
    <th>rank</th>
    <th>model</th>
    <th>comment</th>
  </tr>
  <tr>
    <td rowspan="3"><a href="https://paperswithcode.com/task/3d-human-pose-estimation" title="3d-human-pose-estimation 3D人体姿态估计">body</a></td>
    <td><a href="https://github.com/zju3dv/GVHMR" title="Implementing">🚧GVHMR</a></td>
    <td>VRAM > 3GB </td>
  </tr>
  <tr>
    <td><a href="https://github.com/yufu-wang/tram" title="">TRAM</a></td>
    <td>suit for fast-motion, but VRAM > 6GB</td>
  </tr>
  <tr>
    <td><a href="https://physicalmotionrestoration.github.io/" title="">Plug-and-Play</a></td>
    <td>waiting code release</td>
  </tr>

  <tr>
    <td rowspan="3"><a href="https://paperswithcode.com/task/3d-hand-pose-estimation" title="3d-hand-pose-estimation 3D手部姿态估计">hand</a></td>
    <td><a href="https://github.com/rolpotamias/WiLoR">WiLoR</a>(<a href="https://github.com/warmshao/WiLoR-mini">🚧mini</a>)</td>
    <td>fast, VRAM > 2.5GB, but no constant tracking for video(just no yolo)</td>
  </tr>
  <tr>
    <td><a href="https://github.com/humansensinglab/Hamba">Hamba</a></td>
    <td>after I complete wilor</td>
  </tr>
  <tr>
    <td><a href="https://github.com/amathislab/hoisdf">HOISDF</a></td>
    <td>better on occulusion</td>
  </tr>
  

  <tr>
    <td rowspan="1"><a href="https://paperswithcode.com/task/facial-landmark-detection" title="facial-landmark-detection 面部特征点检测">face</a></td>
    <td><a href="https://github.com/andresprados/SPIGA">SPIGA</a></td>
    <td></td>
  </tr>
</table>

### software:non-OpenSource
- [Look Ma, no markers: holistic performance capture without the hassle](https://www.youtube.com/watch?v=4RkLDW3GmdY)

### hardware:RealTime

<table>
  <tr>
    <th></th>
    <th>solution</th>
    <th>comment</th>
  </tr>

  <tr>
    <td rowspan="2">face</td>
    <td>
      <a href="https://www.ifacialmocap.com/" title="iPhone X + PC(win/Mac)"><i class="fab fa-apple"></i>iFacialMocap</a> |
      <a href="https://suvidriel.itch.io/meowface" title="free, android, can work with iFacialMocap PC client"><i class="fab fa-android"></i> Meowface</a>
    </td>
    <td>shape key</td>
  </tr>
  <tr>
    <td>
      <a href="https://dev.epicgames.com/documentation/en-us/unreal-engine/live-link-in-unreal-engine"><i class="fab fa-apple"></i>unreal live link</a>
    </td>
    <td>bone</td>
  </tr>

  <tr>
    <td rowspan="1">body/hand</td>
    <td>VRchat trackers</td>
    <td><del>off topic</del></td>
  </tr>

</table>

## install
```sh
pip install git+https://github.com/AClon314/mocap-wrapper
mocap -I
```

## usage
```sh
mocap -i input.mp4 output.mp4
```

## dev
You have to read these if you want to modify code.

```sh
LOGLVL=debug mocap -I
```

### [docker](docker/Dockerfile)
```sh
# docker build -t mocap -f docker/Dockerfile .
podman build -t mocap -f docker/Dockerfile . --security-opt label=disable
```

### [requirements](src/mocap_wrapper/requirements/gvhmr.txt)
1. use `mamba`/`conda` to install, so the commented lines are not installed.
2. use `pip` to install the **rest** packages that startwith `# `. So if you want to do comments, you can use `## `or`#...`without space char.

### .npz struct
key: `Armature mapping from`;`Algorithm run`;`who`;`prop[0]`;`prop[1]`...

example: 
- smplx;gvhmr;person0;body_pose;global = array([...], dtype=...)
- smplx;wilor;person1;hand_pose;incam = ...
- smplx;wilor;person1;bbox_xyXY;1 = ... , start from frame 1
- smplx;gvhmr;;K = ... , can leave blank

ps:
the blender addon use `Armature mapping **to**`

#### prop[0]
- pose: thetas, θ
- betas: shape, β
- expression: psi, ψ
- trans(lation) 平移
- global_orient: rotate 旋转
- bbox: yolo_bbox_xyXY