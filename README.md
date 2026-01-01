# mocap-wrapper 动捕套壳
Use with: [mocap_importer](https://github.com/AClon314/mocap_importer_blender)

Wrapping code repositories of various motion capture papers & researches, to provide a unified interface through CLI. Simplify their installation and running.  
Only tested on Linux. Not stable yet.

sincerelly thanks to gvhmr/wilor/wilor-mini developers and others that help each other♥️

## WIP 进展

> [!CAUTION]
> TODO in v0.3:
> - [ ] support Dyn-HaMR, [gvhmr-realtime](https://github.com/MittelmanDaniel/GVHMR-Realtime)
> - [ ] PR udocker for **RESTful over Socket/TCP** in podman standard
> - [ ] support MCP/fastAPI
> - [ ] wilor continuous predict.
> - [ ] ~~PR cockpit compatible with webtui+ chawan(PR websocket) in TUI~~
> - [ ] ~~cockpit **progress** addon(app) with [progress](https://github.com/Xfennec/progress), task-spooler...~~
>   - [ ] ~~progress and [dbus: org.kde.JobTracker](https://github.com/KDE/kjobwidgets/blob/master/src/kstatusbarjobtracker.h) (https://invent.kde.org/frameworks/kjobwidgets/-/merge_requests/6)~~
>   - [ ] ~~new (once) task, pause task if pauseable, stop task, task priority(cpu/gpu hang, network traffic speed limit)~~

| Feature 功能      |                |
| ----------------- | -------------- |
| 🖥Models           | GVHMR, WiLoR   |
| 🐧Linux            | 🚧 Implementing |
| 🪟Windows          | ❓ Need test    |
| 🍎OSX              | ❓              |
| 📔Jupyter Notebook | ❓              |
| 🤖MCP              | 🚧              |
| 🚀国内镜像加速     | ✅              |


## solutions 方案

### software:OpenSource
Rank: [body🕺](https://paperswithcode.com/task/3d-human-pose-estimation "3D人体姿态估计")  [hand👋](https://paperswithcode.com/task/3d-hand-pose-estimation "3D手部姿态估计")  [face👤](https://paperswithcode.com/task/facial-landmark-detection "面部特征点检测") [text to motion文](https://paperswithcode.com/task/motion-synthesis "运动合成(文→动作)")

| model                                                                                                                                                                                                                       | paper                                                                                                                                    | commit                                                                                                                                                                                                                                                            | issue                                                                                                                                                                                                                                          | comment                                                                      |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [✅🕺GVHMR ![⭐](https://img.shields.io/github/stars/zju3dv/GVHMR?style=flat&label=⭐)](https://github.com/zju3dv/GVHMR "World-Grounded Human Motion Recovery via Gravity-View Coordinates")                                    | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.1145/3680528.3687565)](https://doi.org/10.1145/3680528.3687565)           | [![🕒](https://img.shields.io/github/commit-activity/t/zju3dv/GVHMR/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/zju3dv/GVHMR/main?label=🕒)](https://github.com/zju3dv/GVHMR/commits)                                                          | [![🎯](https://img.shields.io/github/issues/zju3dv/GVHMR?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/zju3dv/GVHMR?label=❔)](https://github.com/zju3dv/GVHMR/issues)                                                          | 2024 SIGGRAPH Asia, VRAM > 3GB                                               |
| [🚧🕺TRAM ![⭐](https://img.shields.io/github/stars/yufu-wang/tram?style=flat&label=⭐)](https://github.com/yufu-wang/tram "Global Trajectory and Motion of 3D Humans from in-the-wild Videos")                                 | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.1007/978-3-031-73247-8_27)](https://doi.org/10.1007/978-3-031-73247-8_27) | [![🕒](https://img.shields.io/github/commit-activity/t/yufu-wang/tram/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/yufu-wang/tram/main?label=🕒)](https://github.com/yufu-wang/tram/commits)                                                    | [![🎯](https://img.shields.io/github/issues/yufu-wang/tram?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/yufu-wang/tram?label=❔)](https://github.com/yufu-wang/tram/issues)                                                    | 2024, suit for fast-motion, but VRAM > 6GB                                   |
| [🕒🕺CoMotion ![⭐](https://img.shields.io/github/stars/apple/ml-comotion?style=flat&label=⭐)](https://github.com/apple/ml-comotion "Concurrent Multi-person 3D Motion")                                                       | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2504.12186)](https://doi.org/10.48550/arXiv.2504.12186)       | [![🕒](https://img.shields.io/github/commit-activity/t/apple/ml-comotion/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/apple/ml-comotion/main?label=🕒)](https://github.com/apple/ml-comotion/commits)                                           | [![🎯](https://img.shields.io/github/issues/apple/ml-comotion?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/apple/ml-comotion?label=❔)](https://github.com/apple/ml-comotion/issues)                                           | 2025, belongs to Apple                                                       |
| [🕒🕺SAT-HMR ![⭐](https://img.shields.io/github/stars/ChiSu001/SAT-HMR?style=flat&label=⭐)](https://github.com/ChiSu001/SAT-HMR "Real-Time Multi-Person 3D Mesh Estimation via Scale-Adaptive Tokens")                        | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2411.19824)](https://doi.org/10.48550/arXiv.2411.19824)       | [![🕒](https://img.shields.io/github/commit-activity/t/ChiSu001/SAT-HMR/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/ChiSu001/SAT-HMR/main?label=🕒)](https://github.com/ChiSu001/SAT-HMR/commits)                                              | [![🎯](https://img.shields.io/github/issues/ChiSu001/SAT-HMR?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/ChiSu001/SAT-HMR?label=❔)](https://github.com/ChiSu001/SAT-HMR/issues)                                              | 2025                                                                         |
| [✅👋WiLoR ![⭐](https://img.shields.io/github/stars/rolpotamias/WiLoR?style=flat&label=⭐)](https://github.com/rolpotamias/WiLoR "End-to-end 3D hand localization and reconstruction in-the-wild")                             | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2409.12259)](https://doi.org/10.48550/arXiv.2409.12259)       | [![🕒](https://img.shields.io/github/commit-activity/t/rolpotamias/WiLoR/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/rolpotamias/WiLoR/main?label=🕒)](https://github.com/rolpotamias/WiLoR/commits)                                           | [![🎯](https://img.shields.io/github/issues/rolpotamias/WiLoR?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/rolpotamias/WiLoR?label=❔)](https://github.com/rolpotamias/WiLoR/issues)                                           | 2024, use [mini](https://github.com/warmshao/WiLoR-mini), fast, VRAM > 2.5GB |
| [🚧👋Dyn-HaMR ![⭐](https://img.shields.io/github/stars/ZhengdiYu/Dyn-HaMR?style=flat&label=⭐)](https://github.com/ZhengdiYu/Dyn-HaMR "Recovering 4D Interacting Hand Motion from a Dynamic Camera")                           | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2412.12861)](https://doi.org/10.48550/arXiv.2412.12861)       | [![🕒](https://img.shields.io/github/commit-activity/t/ZhengdiYu/Dyn-HaMR/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/ZhengdiYu/Dyn-HaMR/main?label=🕒)](https://github.com/ZhengdiYu/Dyn-HaMR/commits)                                        | [![🎯](https://img.shields.io/github/issues/ZhengdiYu/Dyn-HaMR?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/ZhengdiYu/Dyn-HaMR?label=❔)](https://github.com/ZhengdiYu/Dyn-HaMR/issues)                                        | 2025 CVPR Highlight                                                          |
| [🕒👋HaWoR ![⭐](https://img.shields.io/github/stars/ThunderVVV/HaWoR?style=flat&label=⭐)](https://github.com/ThunderVVV/HaWoR "World-Space Hand Motion Reconstruction from Egocentric Videos")                                | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2501.02973)](https://doi.org/10.48550/arXiv.2501.02973)       | [![🕒](https://img.shields.io/github/commit-activity/t/ThunderVVV/HaWoR/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/ThunderVVV/HaWoR/main?label=🕒)](https://github.com/ThunderVVV/HaWoR/commits)                                              | [![🎯](https://img.shields.io/github/issues/ThunderVVV/HaWoR?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/ThunderVVV/HaWoR?label=❔)](https://github.com/ThunderVVV/HaWoR/issues)                                              | 2025 CVPR Highlight, for AR/VR headset                                       |
| [🕒👋Hamba ![⭐](https://img.shields.io/github/stars/humansensinglab/Hamba?style=flat&label=⭐)](https://github.com/humansensinglab/Hamba "Single-view 3D Hand Reconstruction withGraph-guided Bi-Scanning Mamba")              | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2407.09646)](https://doi.org/10.48550/arXiv.2407.09646)       | [![🕒](https://img.shields.io/github/commit-activity/t/humansensinglab/Hamba/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/humansensinglab/Hamba/main?label=🕒)](https://github.com/humansensinglab/Hamba/commits)                               | [![🎯](https://img.shields.io/github/issues/humansensinglab/Hamba?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/humansensinglab/Hamba?label=❔)](https://github.com/humansensinglab/Hamba/issues)                               | 2025 NeurIPS                                                                 |
| [🕒👋OmniHands ![⭐](https://img.shields.io/github/stars/LinDixuan/OmniHands?style=flat&label=⭐)](https://github.com/LinDixuan/OmniHands)                                                                                      | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2405.20330)](https://doi.org/10.48550/arXiv.2405.20330)       | [![🕒](https://img.shields.io/github/commit-activity/t/LinDixuan/OmniHands/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/LinDixuan/OmniHands/main?label=🕒)](https://github.com/LinDixuan/OmniHands/commits)                                     | [![🎯](https://img.shields.io/github/issues/LinDixuan/OmniHands?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/LinDixuan/OmniHands?label=❔)](https://github.com/LinDixuan/OmniHands/issues)                                     | 2024                                                                         |
| [🕒👋HaMeR ![⭐](https://img.shields.io/github/stars/geopavlakos/hamer?style=flat&label=⭐)](https://github.com/geopavlakos/hamer "Hand Mesh Recovery")                                                                         | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2312.05251)](https://doi.org/10.48550/arXiv.2312.05251)       | [![🕒](https://img.shields.io/github/commit-activity/t/geopavlakos/hamer/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/geopavlakos/hamer/main?label=🕒)](https://github.com/geopavlakos/hamer/commits)                                           | [![🎯](https://img.shields.io/github/issues/geopavlakos/hamer?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/geopavlakos/hamer?label=❔)](https://github.com/geopavlakos/hamer/issues)                                           | 2023                                                                         |
| [🕒👋HOISDF ![⭐](https://img.shields.io/github/stars/amathislab/hoisdf?style=flat&label=⭐)](https://github.com/amathislab/hoisdf "Constraining 3D Hand-Object Pose Estimation with Global Signed Distance Fields")            | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.1109/CVPR52733.2024.00989)](https://doi.org/10.1109/CVPR52733.2024.00989) | [![🕒](https://img.shields.io/github/commit-activity/t/amathislab/hoisdf/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/amathislab/hoisdf/main?label=🕒)](https://github.com/amathislab/hoisdf/commits)                                           | [![🎯](https://img.shields.io/github/issues/amathislab/hoisdf?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/amathislab/hoisdf?label=❔)](https://github.com/amathislab/hoisdf/issues)                                           | 2024, better on occulusion                                                   |
| [🕒👤SPIGA ![⭐](https://img.shields.io/github/stars/andresprados/SPIGA?style=flat&label=⭐)](https://github.com/andresprados/SPIGA "Shape Preserving Facial Landmarks with Graph Attention Networks")                          | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2210.07233)](https://doi.org/10.48550/arXiv.2210.07233)       | [![🕒](https://img.shields.io/github/commit-activity/t/andresprados/SPIGA/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/andresprados/SPIGA/main?label=🕒)](https://github.com/andresprados/SPIGA/commits)                                        | [![🎯](https://img.shields.io/github/issues/andresprados/SPIGA?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/andresprados/SPIGA?label=❔)](https://github.com/andresprados/SPIGA/issues)                                        | 2022                                                                         |
| [🕒👤mediapipe ![⭐](https://img.shields.io/github/stars/google-ai-edge/mediapipe?style=flat&label=⭐)](https://github.com/google-ai-edge/mediapipe "Cross-platform, customizable ML solutions for live and streaming media. ") | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2006.10204)](https://doi.org/10.48550/arXiv.2006.10204)       | [![🕒](https://img.shields.io/github/commit-activity/t/google-ai-edge/mediapipe/master?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/google-ai-edge/mediapipe/master?label=🕒)](https://github.com/google-ai-edge/mediapipe/commits)                  | [![🎯](https://img.shields.io/github/issues/google-ai-edge/mediapipe?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/google-ai-edge/mediapipe?label=❔)](https://github.com/google-ai-edge/mediapipe/issues)                      | realtime                                                                     |
| [🕒文🎵 MotionAnything ![⭐](https://img.shields.io/github/stars/steve-zeyu-zhang/MotionAnything?style=flat&label=⭐)](https://github.com/steve-zeyu-zhang/MotionAnything)                                                      | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2503.06955)](https://doi.org/10.48550/arXiv.2503.06955)       | [![🕒](https://img.shields.io/github/commit-activity/t/steve-zeyu-zhang/MotionAnything/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/steve-zeyu-zhang/MotionAnything/main?label=🕒)](https://github.com/steve-zeyu-zhang/MotionAnything/commits) | [![🎯](https://img.shields.io/github/issues/steve-zeyu-zhang/MotionAnything?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/steve-zeyu-zhang/MotionAnything?label=❔)](https://github.com/steve-zeyu-zhang/MotionAnything/issues) | 2025, waiting code release                                                   |
| [🕒文 momask-codes ![⭐](https://img.shields.io/github/stars/EricGuo5513/momask-codes?style=flat&label=⭐)](https://github.com/EricGuo5513/momask-codes)                                                                       | [![cite🙶](https://api.juleskreuer.eu/citation-badge.php?doi=10.48550/arXiv.2312.00063)](https://doi.org/10.48550/arXiv.2312.00063)       | [![🕒](https://img.shields.io/github/commit-activity/t/EricGuo5513/momask-codes/main?label=🕒) ![LAST🕒](https://img.shields.io/github/last-commit/EricGuo5513/momask-codes/main?label=🕒)](https://github.com/EricGuo5513/momask-codes/commits)                      | [![🎯](https://img.shields.io/github/issues/EricGuo5513/momask-codes?label=⁉️) ![🎯close](https://img.shields.io/github/issues-closed/EricGuo5513/momask-codes?label=❔)](https://github.com/EricGuo5513/momask-codes/issues)                      | 2024                                                                         |
- hand: no constant tracking for video(just no yolo, ready for photo but not video)

### software:non-OpenSource
- [🕺👋👤-文🎵 Genmo （Nvidia Lab）](https://research.nvidia.com/labs/dair/genmo/)
- [🕺👋👤Look Ma, no markers: holistic performance capture without the hassle](https://www.youtube.com/watch?v=4RkLDW3GmdY)
- [👤D-ViT](https://arxiv.org/abs/2411.07167v1 "Cascaded Dual Vision Transformer for Accurate Facial Landmark Detection")

### hardware:RealTime
|           | Solution                                                                                                                                                                           | Comment       |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 👤face     | [🍎iFacialMocap](https://www.ifacialmocap.com/) (iPhone X + PC(win/Mac)) <br> [🤖Meowface](https://suvidriel.itch.io/meowface) (free, Android, can work with iFacialMocap PC client) | Shape key     |
|           | [🍎+💻Unreal Live Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/live-link-in-unreal-engine)                                                                      | Bone          |
| hand/body | VR headset or VR trackers                                                                                                                                                          | ~~Off topic~~ |
- *🍎`iphone≥X(12/13 best)`for **better face mocap result** on UE live link, though you can use android🤖 to do live link.*

## install 安装
The scripts will smartly skip or update `pixi,uv,mocap-wrapper,7z,aria2c,ffmpeg,git` if they're installed or in system $PATH.

```sh
# sudo -i; bash <(curl -sSL https://gitee.com/SuperManito/LinuxMirrors/raw/main/ChangeMirrors.sh) # 一键设置linux镜像(可选)
curl https://raw.githubusercontent.com/AClon314/mocap-wrapper/refs/heads/master/src/mocap_wrapper/install/pixi.py | python -- -y
mocap --install -b gvhmr,wilor
```

The python scripts are equivalent to the following:
```bash
#!/bin/bash -eou pipefail
# 1. pixi.py
curl -fsSL https://pixi.sh/install.sh | sh
pixi global install uv
uv python install
~/.pixi/bin/uv pip install git+https://github.com/AClon314/mocap-wrapper

# 2. mocap --install -b ''
sudo apt install 7z aria2 ffmpeg git # pixi global install 7z aria2 ffmpeg git
git clone https://github.com/zju3dv/GVHMR
aria2c hmr4d.ckpt   # download pre-trained

# 3. mocap-wrapper in uv; gvhmr/wilor... in pixi env seperately
. ~/.venv/bin/activate
mocap -i input.mp4 -b gvhmr
cd $SEARCH_DIR/GVHMR
pixi run run/gvhmr.py
```

```mermaid
%%{init:{'flowchart':{'padding':0, 'htmlLabels':false}, 'htmlLabels':false, 'theme':'base', 'themeVariables':{'primaryColor':'#fff','clusterBkg':'#fff','edgeLabelBackground':'#fff','lineColor':'#888','primaryTextColor':'#000','primaryBorderColor':'#000','secondaryTextColor':'#000', 'clusterBorder':'#888','tertiaryTextColor':'#000'} }}%%
graph TD
pkgs["7z,aria2c,ffmpeg, podman/udocker"]
ai["gvhmr,wilor..."]
pixi --global install--> uv
uv --~/.venv--> mocap
mocap --global install--> pkgs
pkgs -.container.-> ai
```

## usage 用法
See `mocap -h` for more options.
```sh
mocap -i input.mp4
mocap -i input.mp4 -b gvhmr,wilor -o outdir
```

### [data_viewer.ipynb](tests/data_viewer.ipynb)

A useful data visualize tool for .pt/.npy/.npz

![vscode data wrangler](https://code.visualstudio.com/assets/docs/datascience/data-wrangler/full-dw-loop.gif)

## dev 开发
You have to read these if you want to modify code.

```sh
LOG=debug mocap -I
```

```
❯ tree -L 2 --gitignore
.
├── api  # connect-rpc api convention & code generation from
├── docker  # github action CI build docker image
├── pyproject.toml
├── pytest.ini
├── setup.py
├── src
│   └── mocap_wrapper # python backend package
├── tests
│   ├── bbox_yolo_viewer.js # TODO
│   ├── data_viewer.ipynb # mentioned above
│   ├── docker.sh
│   ├── test_install.py
│   ├── test_lib.py
│   └── test_script.py
└── web # frontend web UI dashboard panel
    ├── astro.config.mjs
    ├── package.json
    ├── public
    ├── README.md
    ├── src
    └── tsconfig.json
```

### [docker](container/Dockerfile)
```sh
# docker build -t mocap -f docker/Dockerfile .
podman build -t mocap -f docker/Dockerfile . --security-opt label=disable
# github action local
act -j test -v --action-offline-mode --bind --reuse --env LOG=D # --rm=false
```

### .npz struct
key: `Armature mapping from`;`Algorithm run`;`who`;`begin`;`prop[0]`;`prop[1]`...

example: 
- smplx;gvhmr;person0;0;body_pose = array([...], dtype=...)
- smplx;wilor;person1;9;hand_pose = ...
- smplx;wilor;person1;1;bbox = ...

ps: the blender addon use *Armature mapping **to***

#### prop[0]
- pose: thetas, θ
- betas: shape, β
- expression: psi, ψ
- trans(lation) 平移
- global_orient: rotate 旋转
- bbox: yolo_bbox_xyXY

## Licenses 协议
By using this repository, you must also comply with the terms of these external licenses:

| Repo          | License                                                                                                                                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GVHMR         | [Copyright 2022-2023 3D Vision Group at the State Key Lab of CAD&CG, Zhejiang University. All Rights Reserved. ![CC BY-NC-SA](https://licensebuttons.net/l/by-nc-sa/3.0/88x31.png)](https://github.com/zju3dv/GVHMR/blob/main/LICENSE "CC BY-NC-SA") |
| WiLoR         | [![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/3.0/88x31.png)](https://github.com/rolpotamias/WiLoR/blob/main/license.txt "CC BY-NC-ND 4.0")                                                                                              |
| mocap-wrapper | [AGPL v3](./LICENSE)                                                                                                                                                                                                                                 |

## Dev Log 开发者日志
- 2025.12.08: 
1个月停更是去探索CLI/TUI/webUI的跨平台方案了。 摸索出:
    - CLI: python argParse+argcomplete **客户端**参数转pandatic http请求
      - fastAPI **服务器**任务调度/网络请求
      - podman udocker CLI调用 或 ~~json-RPC通信~~
    - TUI: chawan 网页浏览器(nim语言，导入websocket C库成功，但nim lang server类型提示没弄出来，遂放弃)
    - webUI: webTUI css 主题; cockpit webUI 自带简易身份认证; cockpit 任务队列插件;
综上，这是我对此项目最终的愿景，这里就已经涉及到5个大工程了。个人开发精力有限，最后决定先让项目跑起来，以后有时间慢慢迭代这些 **重要但不紧急**的需求。 