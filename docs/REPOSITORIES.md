# Selected Blender and animation repositories

These are the 11 repositories previously selected for character, motion and VFX work. They are **optional references and tools**, not dependencies of Blender MCP. Exact observed commits are in [repositories.json](repositories.json). This repository does not bundle their code, assets, weights or environments.

## Characters and rigging

| Repository | Use it for | Integration decision |
| --- | --- | --- |
| [MB-Lab](https://github.com/animate1978/MB-Lab) | Parametric humanoid geometry, anatomy and existing character data | The prior character builder directly used MB-Lab's data. Its checked README targets Blender 4.0+. Verify actual 5.2 compatibility before enabling the add-on; data reuse and add-on execution are separate choices. |
| [MPFB2](https://github.com/makehumancommunity/mpfb2) | Human generation and a MakeHuman-oriented character workflow | The checked README requires Blender 4.2 or newer. Prefer evaluating this maintained workflow for a fresh humanoid; that version floor alone does not prove compatibility with every later Blender release. |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | Learned skeleton generation and skin weights for an existing mesh | Evaluate when automatic rigging saves work. The checked README states at least 8 GB CUDA VRAM for generation. Use its official installation/export path and validate bone axes, skin weights and Blender import; a mesh still needs motion retargeting afterward. |

Claude: choose one humanoid workflow, build a clean neutral character, and validate shoulders, elbows, wrists, hips and knees with natural movement before elaborate action. Do not combine two generators' rigs without a deliberate retargeting plan. Match the target Blender version before installing an add-on.

## Motion and capture

| Repository | Use it for | Integration decision |
| --- | --- | --- |
| [FreeMoCap](https://github.com/freemocap/freemocap) | Capture actual human motion from video and export supported results to Blender | Best first choice when footage can supply the movement. Keep its version and tracking backend explicit. The current release line and historical checkout can use different installers and export capabilities. |
| [HY-Motion-1.0](https://github.com/Tencent-Hunyuan/HY-Motion-1.0) | Text-generated motion to retarget to a humanoid | The checked README lists 26 GB minimum VRAM for the full model and 24 GB for Lite, excluding optional prompt-engineering overhead. A 4090 does not automatically make the full model fit. Evaluate Lite and its documented short-clip settings only when needed. |
| [motion-diffusion-model](https://github.com/GuyTevet/motion-diffusion-model) | Research-oriented text-to-motion generation and editing | Expect dataset/model preparation, skeleton conversion and dependency licenses. Generated motion is not automatically an animation on the final character's rig. |
| [AI4Animation](https://github.com/sebastianstarke/AI4Animation) | Locomotion, transitions, contacts and motion-model research | The checked checkout includes newer Python/NumPy/PyTorch work as well as historical Unity examples. Its README restricts research/education use and mocap data redistribution; check the relevant terms before using outputs commercially. |
| [DeepMimic](https://github.com/xbpeng/DeepMimic) | Physics-based imitation research and reference motions | Its README marks the project deprecated and points to MimicKit. Keep it as historical prior art rather than the default installation for a new Blender scene. |

Claude: prefer recorded or existing motion when it meets the shot. Check frame rate, scale, root translation, bone mapping, foot contact and hand contact after retargeting. Use generated or research motion when it solves a concrete missing movement, and test a short segment first. Do not install several large ML stacks into the MCP or Blender Python environment.

### iPhone footage with FreeMoCap

The intended first test is **record on iPhone → transfer the video → import/process on the PC → export supported motion to Blender → retarget and clean up**. FreeMoCap supports imported videos; its release notes describe synchronization by audio or brightness. This does not establish native iPhone live-USB camera support.

For a first recording, use a fixed camera, good light, the whole body in frame, and a simple movement without prolonged occlusion. Check imported timing, orientation and actual frame rate. One camera is useful for a first reconstruction; calibrated multiple views improve geometric depth and occlusion coverage. Do not describe a single view as equivalent to calibrated multi-camera capture.

Sources: [FreeMoCap single-camera workflow](https://docs.freemocap.org/documentation/single-camera-recording.html), [official release notes for importing, synchronization and Blender export changes](https://github.com/freemocap/freemocap/releases). This test was deferred; installing MCP must not trigger it.

## Particles and volumes

| Repository | Use it for | Integration decision |
| --- | --- | --- |
| [Effekseer](https://github.com/effekseer/Effekseer) | Particle timing, bursts, layered energy effects and practical effect-authoring references | It is a standalone particle editor/runtime ecosystem, primarily aimed at games. Do not assume its effects import into Blender as editable native nodes. Choose a documented export/compositing route or rebuild the needed visual behavior with native Blender tools. |
| [OpenVDB](https://github.com/AcademySoftwareFoundation/openvdb) | Sparse volume representation for smoke, dust and volumetric effects | Use Blender's supported volume workflow or existing VDB assets first. Building the C++ library from source is not required merely to render a volume in Blender. |
| [TRELLIS](https://github.com/microsoft/TRELLIS) | Generating candidate 3D assets from images | Useful for initial objects when clean topology or an existing library asset is unavailable. The checked README reports Linux-tested support, unverified Windows guidance, at least 16 GB VRAM and CUDA compilation dependencies. Treat native Windows setup as a separate investigation, not part of the MCP installer. |

Claude: for a shockwave, define propagation direction, impact timing and physical response first. Use layered pressure distortion, debris and dust appropriate to the shot; a wandering ring is not a substitute for a directed shock front. For an orb, validate the silhouette, transparency, light spill and tracked placement against the actual background. More emission strength does not create realism by itself.

## How Claude should select and clone a repository

1. Name the missing capability and select the smallest relevant repository or native Blender feature.
2. Read its official README, release/install instructions and license. Use the exact historical commit in repositories.json when reproducing the previously inspected state; use a newer release only as an explicit change with new compatibility checks.
3. Clone only that repository into the ignored local repos/ directory. Example:

```powershell
git clone https://github.com/makehumancommunity/mpfb2.git repos/mpfb2
git -C repos/mpfb2 checkout 3af0cd5a2ffba072e93a34e5f6f494fdc4813ddf
```

4. Use a separate environment for ML or capture dependencies. Confirm required weights and their licenses before downloading them.
5. Import or apply a small result, then verify it in Blender using MCP and an actual preview. Report which capability was reused; do not say a repository was used merely because it was cloned.

The recorded checkouts are historical references, not a claim that every tool has been tested on Windows or Blender 5.2. None of these repositories needs to be installed before the core MCP connection test passes.
