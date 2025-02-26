<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" integrity="sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==" crossorigin="anonymous" referrerpolicy="no-referrer" />

# mocap-wrapper


## solutions
### software:OpenSource

<table>
  <tr>
    <th>rank</th>
    <th>model</th>
    <th>comment</th>
  </tr>
  <tr>
    <td rowspan="2"><a href="https://paperswithcode.com/task/3d-human-pose-estimation" title="3d-human-pose-estimation 3D人体姿态估计">body</a></td>
    <td><a href="https://github.com/zju3dv/GVHMR" title="Implementing">🚧GVHMR</a></td>
    <td></td>
  </tr>
  <tr>
    <td><a href="https://github.com/yufu-wang/tram" title="">TRAM</a></td>
    <td>suit for fast-motion, but high VRAM usage</td>
  </tr>

  <tr>
    <td rowspan="3"><a href="https://paperswithcode.com/task/3d-hand-pose-estimation" title="3d-hand-pose-estimation 3D手部姿态估计">hand</a></td>
    <td><a href="https://github.com/rolpotamias/WiLoR">WiLoR</a>(<a href="https://github.com/warmshao/WiLoR-mini">🚧mini</a>)</td>
    <td>fast, low VRAM usage: 2.5GB</td>
  </tr>
  <tr>
    <td><a href="https://github.com/amathislab/hoisdf">HOISDF</a></td>
    <td>better on occulusion</td>
  </tr>
  <tr>
    <td><a href="https://github.com/humansensinglab/Hamba">Hamba</a></td>
    <td>waiting code release</td>

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
```

```

## usage
```
mocap -I -i input.mp4 output.mp4
```