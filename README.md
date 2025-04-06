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
      <a href="https://www.ifacialmocap.com/" title="iPhone X + PC(win/Mac)"><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>iFacialMocap</a> |
      <a href="https://suvidriel.itch.io/meowface" title="free, android, can work with iFacialMocap PC client"><svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M420.6 301.9a24 24 0 1 1 24-24 24 24 0 0 1 -24 24m-265.1 0a24 24 0 1 1 24-24 24 24 0 0 1 -24 24m273.7-144.5 47.9-83a10 10 0 1 0 -17.3-10h0l-48.5 84.1a301.3 301.3 0 0 0 -246.6 0L116.2 64.5a10 10 0 1 0 -17.3 10h0l47.9 83C64.5 202.2 8.2 285.6 0 384H576c-8.2-98.5-64.5-181.8-146.9-226.6"/></svg> Meowface</a>
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

## Licenses
Please refer to their respective licenses for more details:

| Dependency| License
|-|-|
|GVHMR|≈[![CC BY-NC-SA](https://licensebuttons.net/l/by-nc-sa/3.0/88x31.png)](https://github.com/zju3dv/GVHMR/blob/main/LICENSE "CC BY-NC-SA")
|WiLoR| [![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/3.0/88x31.png)](https://github.com/rolpotamias/WiLoR/blob/main/license.txt "CC BY-NC-ND 4.0")
|mocap-wrapper| [AGPL v3](./LICENSE)