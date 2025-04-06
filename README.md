# mocap-wrapper
Addon: [mocap_importer](https://github.com/AClon314/mocap_importer_blender)

A bunch of python scripts that wrap around various mocap libraries to provide a unified interface.  
Only tested on Linux. Not stable yet.

sincerelly thanks to gvhmr/wilor/wilor-mini developers and others that help each other♥️
## solutions
### software:OpenSource
hand: no constant tracking for video(just no yolo, ready for photo but not video)

<table>
  <tr>
    <th>rank</th>
    <th>model</th>
    <th>comment</th>
  </tr>
  <tr>
    <td rowspan="3"><a href="https://paperswithcode.com/task/3d-human-pose-estimation" title="3d-human-pose-estimation 3D人体姿态估计">body</a></td>
    <td><a href="https://github.com/zju3dv/GVHMR" title="Implementing">✅GVHMR</a></td>
    <td>VRAM > 3GB </td>
  </tr>
  <tr>
    <td><a href="https://github.com/yufu-wang/tram" title="">🕒TRAM</a></td>
    <td>suit for fast-motion, but VRAM > 6GB</td>
  </tr>
  <tr>
    <td><a href="https://physicalmotionrestoration.github.io/" title="">🕒Plug-and-Play</a></td>
    <td>waiting code release</td>
  </tr>

  <tr>
    <td rowspan="4"><a href="https://paperswithcode.com/task/3d-hand-pose-estimation" title="3d-hand-pose-estimation 3D手部姿态估计">hand</a></td>
    <td><a href="https://github.com/rolpotamias/WiLoR">WiLoR</a>(<a href="https://github.com/warmshao/WiLoR-mini">🚧mini</a>)</td>
    <td>fast, VRAM > 2.5GB</td>
  </tr>
  <tr>
    <td><a href="https://github.com/humansensinglab/Hamba">🕒Hamba</a></td>
    <td>2025</td>
  </tr>
   <tr>
    <td><a href="https://github.com/geopavlakos/hamer">🕒HaMeR</a></td>
    <td>2024</td>
  </tr>
  <tr>
    <td><a href="https://github.com/amathislab/hoisdf">🕒HOISDF</a></td>
    <td>better on occulusion</td>
  </tr>
  

  <tr>
    <td rowspan="1"><a href="https://paperswithcode.com/task/facial-landmark-detection" title="facial-landmark-detection 面部特征点检测">face</a></td>
    <td><a href="https://github.com/andresprados/SPIGA">🕒SPIGA</a></td>
    <td></td>
  </tr>
</table>

### software:non-OpenSource
- [Look Ma, no markers: holistic performance capture without the hassle](https://www.youtube.com/watch?v=4RkLDW3GmdY)

### hardware:RealTime
<style>
.icon {
  width: 1em;
  height: 1em;
  vertical-align: -0.125em;
}
</style>
<table>
  <tr>
    <th></th>
    <th>solution</th>
    <th>comment</th>
  </tr>

  <tr>
    <td rowspan="2">face</td>
    <td>
      <a href="https://www.ifacialmocap.com/" title="iPhone X + PC(win/Mac)">🍎iFacialMocap</a> | 
      <a href="https://suvidriel.itch.io/meowface" title="free, android, can work with iFacialMocap PC client">🤖 Meowface</a>
    </td>
    <td>shape key</td>
  </tr>
  <tr>
    <td>
      <a href="https://dev.epicgames.com/documentation/en-us/unreal-engine/live-link-in-unreal-engine">🍎+💻unreal live link</a>
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

## Licenses
By using this repository, you must also comply with the terms of these external licenses:

| Repo | License |
|-|-|
|GVHMR|[Copyright 2022-2023 3D Vision Group at the State Key Lab of CAD&CG, Zhejiang University. All Rights Reserved. ![CC BY-NC-SA](https://licensebuttons.net/l/by-nc-sa/3.0/88x31.png)](https://github.com/zju3dv/GVHMR/blob/main/LICENSE "CC BY-NC-SA")
|WiLoR| [![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/3.0/88x31.png)](https://github.com/rolpotamias/WiLoR/blob/main/license.txt "CC BY-NC-ND 4.0")
|mocap-wrapper| [AGPL v3](./LICENSE)