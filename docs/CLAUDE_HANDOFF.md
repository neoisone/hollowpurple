# Blender MCP setup for Claude on Windows with RTX 4090

Use this repository to start **new Blender work** on a Windows PC. It contains setup code and instructions only. No previous scenes, renders, footage, model weights or asset libraries need to be transferred.

The normal route is to run the commands in README.md. Feed this document and CLAUDE.md into Claude when help is needed; the Python commands perform the setup and checks without requiring an LLM to reinvent them.

## Goal and verified pipeline

The integration is Siddharth Ahuja's existing [MCP for Blender](https://github.com/ahujasid/mcp-for-blender), not a custom server. The original Mac registration used uvx and an unpinned mcp-for-blender command. Its installed add-on exactly matched package **2.1.9**, add-on **1.8**, protocol **13**. That is the reproducibility baseline here.

This repository improves the launcher for portability: Claude starts the absolute **uv.exe** executable with **run --frozen --project <absolute repository path> --python 3.11 mcp-for-blender**. Both the client and the check script therefore use this repository's locked environment rather than resolving a separate uvx environment each time. The package and Blender bridge remain the same.

```text
Claude Desktop OR native Windows Claude Code
  -> uv.exe run --frozen --project <this checkout> ...
    -> mcp-for-blender 2.1.9 over MCP stdio
      -> localhost:9876 Blender socket
        -> matching add-on inside the normal Blender GUI
          -> Blender Python, scene inspection and image/viewport tools

Cycles rendering: RTX 4090 through OptiX
Long rendering jobs: separate background blender.exe processes
```

The local socket is not an HTTP endpoint. Do not add http://localhost:9876 as a remote Claude connector. A browser-only Claude conversation cannot launch this local stdio process.

The pinned package requires MCP Python SDK version 1.x. The lockfile preserves that compatible SDK and its dependencies. Do not replace it with SDK 2.x examples or run unpinned global packages to diagnose this environment.

### Reuse and setup choices

| Existing capability | How it is reused |
| --- | --- |
| Upstream addon_manager.install_addon | Copies the exact bundled add-on and preserves its existing backup behavior. |
| Upstream find_existing_addon_installs | Detects older directory-style package add-ons before installation. |
| Upstream setup_cli discovery | Finds Blender and Claude clients, including the Windows Store Claude configuration location. |
| Upstream read_json_config | Reads existing client settings; unrelated entries remain intact. |
| Upstream blender_is_running | Uses the package's OEM-aware Windows process handling. |
| Upstream safe_to_save_prefs and enable_addon_headless | Avoids taking over first-run settings migration and enables the add-on only when appropriate. |
| Official MCP Python SDK | Performs real initialization and tool calls in pipeline.check_mcp. |
| Blender Cycles | Provides rendering; pipeline.configure_gpu selects the intended backend and device. |

New code supplies the frozen launch arguments, focused config merging and rollback, explicit GPU selection, result validation and a fresh smoke scene. It does not introduce another MCP protocol or asset pipeline.

Alternatives considered: latest automatic upstream setup is convenient but changes the version baseline; a source fork adds maintenance without helping normal scene creation. The pinned package with a small setup layer is the chosen route. Upgrade the package and its add-on together when deliberately changing that baseline.

This setup changes local client/add-on configuration only when --apply is supplied. It requires no shared schema, database, cloud deployment or public network listener. Existing Blender work stays untouched. Optional research tools are selected per creative task, not installed as part of the connection.

## Windows setup

Use native Windows PowerShell. WSL introduces different filesystem and localhost boundaries and is not the baseline for this setup.

### Install prerequisites

1. Install Blender **5.2** from the [official download site](https://www.blender.org/download/). The original verified version was 5.2.2 LTS. Open it once, finish any settings migration, then save and close it.
2. Install a compatible NVIDIA driver. Confirm nvidia-smi identifies the RTX 4090. Use the current [Blender requirements](https://www.blender.org/download/requirements/) for the chosen Blender version.
3. Install and sign into Claude Desktop or Claude Code.
4. Install uv and Git with WinGet if missing, then reopen PowerShell:

```powershell
winget install --id astral-sh.uv -e
winget install --id Git.Git -e
uv --version
git --version
nvidia-smi
```

The setup uses uv-managed Python 3.11. Blender uses its own embedded Python. Do not install bpy into the external MCP environment. A standard Blender installation does not require a CUDA development toolkit merely to render with OptiX.

Sources: [uv installation](https://docs.astral.sh/uv/getting-started/installation/), [uv Python management](https://docs.astral.sh/uv/guides/install-python/), [NVIDIA application GPU setup](https://nvidia.custhelp.com/app/answers/detail/a_id/5188).

### Clone and inspect

The repository is public and can be cloned without account access:

```powershell
git clone https://github.com/neoisone/hollowpurple.git
cd hollowpurple
uv sync --frozen --python 3.11
uv run --frozen python -m pipeline.setup_windows --client desktop
```

Use --client code for Claude Code. Inspection prints the real configuration path, actual Blender paths, server launch arguments and intended changes. It does not install the add-on or write client configuration.

Discovery can be overridden explicitly:

```powershell
uv run --frozen python -m pipeline.setup_windows --client desktop --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

That Blender path is an example; use the installed executable. The --config option overrides the Desktop configuration path when necessary. The --uv option overrides the discovered uv.exe executable. A different Blender major/minor baseline requires --allow-version-mismatch; that flag permits a deliberate compatibility test and does not prove support.

### Apply the setup

Save and close Blender. Close Claude Desktop before editing its configuration, then run:

```powershell
uv run --frozen python -m pipeline.setup_windows --client desktop --apply
```

The script:

- Reuses the pinned package's add-on installer and verifies the installed file's hash.
- Merges the Blender entry into Desktop settings, retaining unrelated servers and preferences.
- Uses Claude Code's own CLI for its user-scoped registration when --client code is selected.
- Backs up changed client configuration and restores it if a CLI replacement fails; a failed first-time CLI write removes the partial new file.
- Refuses a conflicting blender entry unless --replace-existing is explicitly supplied.
- Rejects an old directory-style MCP package add-on for manual migration, avoiding two competing copies.
- Enables the add-on through upstream helpers if saving preferences is appropriate. If first-run migration must be finished, it gives the manual enable step instead.

The expected bundled blender_mcp.py SHA-256 is:

```text
eb0facf69781a30e69792532087d8d41c6a14fcd323353250abe7988ee297fa5
```

The actual add-on directory is probed inside Blender; it is not assumed from a Mac path. The usual Windows folder is %APPDATA%\Blender Foundation\Blender\5.2\scripts\addons. An add-on installation and an external MCP package installation are separate steps.

Source: [pinned package distribution](https://pypi.org/project/mcp-for-blender/2.1.9/), [upstream installation](https://www.mcp-for-blender.com/docs/installation).

## Claude connection

### Claude Desktop

The ordinary configuration is %APPDATA%\Claude\claude_desktop_config.json. The Microsoft Store build can use a redirected package location instead. The setup reuses upstream detection; Settings → Developer → Edit Config identifies the application’s real file when there is ambiguity.

The generated entry contains an absolute uv.exe path and an absolute --project path, so the GUI does not need the terminal's current directory. It sets UV_PYTHON_PREFERENCE=only-managed, BLENDER_HOST=localhost, BLENDER_PORT=9876 and DISABLE_TELEMETRY=1. The telemetry setting applies to the MCP package, not to Claude's own service policies.

Fully quit and reopen Desktop after configuration. Enable the Blender tools for the conversation if needed. An organization policy can restrict local integrations. Desktop MCP supplies Blender tools; it does not automatically provide a general-purpose terminal. Claude Code is the closer match for running local scripts and encoding jobs.

Sources: [local MCP setup](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers), [Claude local MCP guidance](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

### Claude Code

If needed:

```powershell
winget install --id Anthropic.ClaudeCode -e
```

Reopen the terminal, verify claude --version and complete sign-in. Run the setup commands with --client code. The script registers a user-scoped stdio server, with Claude's options before the server name and -- before the server command. It keeps machine-specific paths out of shared project configuration. Start a new Claude Code session afterward and inspect /mcp.

Sources: [Claude Code Windows setup](https://code.claude.com/docs/en/setup), [MCP registration and scopes](https://code.claude.com/docs/en/mcp).

### Verify the actual bridge

Open Blender with its GUI. In Preferences → Add-ons, enable MCP for Blender if needed. In the 3D Viewport, press N and inspect the MCP for Blender tab. Start its listener if it is not running.

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 9876
uv run --frozen python -m pipeline.check_mcp
```

TCP success proves only that a socket is listening. The Python check additionally initializes the real MCP process, verifies required tools, validates protocol 13, reads scene information and runs a small Blender Python inspection. It makes no language-model API request.

In Claude, ask it to call get_addon_status and get_scene_info and show the result with look. This validates tool availability in the chosen client as well as the independent Python check.

## RTX 4090 rendering

Configure the active live Blender scene through the same connection:

```powershell
uv run --frozen python -m pipeline.check_mcp --configure-gpu
```

pipeline/configure_gpu.py selects **Cycles**, **OPTIX**, an OptiX device whose name contains **4090**, and **GPU** for the active scene. It disables other device entries for that operation, enables adaptive sampling and OpenImageDenoise, and prints the configuration. It fails if the requested device is unavailable. It does not silently render on CPU or save global preferences.

Manual equivalent: Preferences → System → Cycles Render Devices → OptiX → RTX 4090, then Render Properties → Cycles → GPU Compute. Configure each render scene; selecting a device in Preferences alone does not set every scene.

Create and render a new test scene in a separate background process:

```powershell
$BlenderExe = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $BlenderExe --background --python-exit-code 1 --python "$PWD\pipeline\smoke_scene.py" -- --output "$PWD\runtime\smoke-4090"
```

The script requires a background process because it resets that process to an empty scene. It refuses a nonempty output directory. It writes a plane, red emissive sphere, glass object, camera and light, then saves mcp_smoke.blend, smoke.png and report.json. The default is 512×512, 64 samples and OptiX/4090. --backend CPU exists for an explicit CPU validation run; it is never a fallback.

Open the image and inspect it. Device settings are not measured hardware-use evidence: check nvidia-smi or a GPU compute graph while a representative render runs. Record resolution, samples, backend and time together. The 4090 accelerates supported local work, not the hosted Claude model. Physics, scene operations and other tools can still use the CPU.

For production, begin with a short preview. Increase quality only after checking materials, geometry, reflections, transmission, light placement and temporal noise. GPU power does not repair opaque glass or poor animation. Frame sequences preserve completed work if a long render stops.

Sources: [Blender GPU rendering](https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html), [NVIDIA GPU configuration](https://nvidia.custhelp.com/app/answers/detail/a_id/5188).

## New project workflow

Keep the repository in a stable local directory. The client registration contains its absolute path; if you move the checkout, rerun setup deliberately to update the entry.

Create new scenes in projects/ and renders in runtime/ or renders/. They are ignored by Git. The repository has no old scenes, user footage, research environments or large model files. No Git LFS setup is required.

Read REPOSITORIES.md when a task needs humanoids, rigging, motion capture, generated motion, particles or volumes. It covers the 11 selected repositories and links to their official sources. Clone only the chosen tool into the ignored repos/ folder, keep ML environments separate, inspect compatibility and license terms, and validate a small result in Blender. Do not install them all during MCP setup.

For substantial new work: inspect the scene, save a checkpoint, make a small change, view it through MCP, render a representative frame, then proceed. A separate background Blender process does not automatically change what the live GUI shows; open the saved result in the GUI when needed.

The iPhone/FreeMoCap test was deferred. Its future recorded-video workflow is documented in REPOSITORIES.md and must not run as part of this setup.

## Claude handoff prompt

```text
Use this checkout to set up Blender MCP on my native Windows PC with RTX 4090.
Read README.md and CLAUDE.md, then use the existing Python commands. Do not
build another MCP server or install every optional research repository.

Inspect the actual Blender, uv and client installation. Use the pinned
mcp-for-blender 2.1.9 package, matching protocol-13 add-on and frozen project
environment. Run pipeline.setup_windows for my chosen client in inspection
mode, then perform the authorized setup with --apply. Preserve existing
configuration and stop on a concrete conflict instead of overwriting it.
If this client cannot execute local commands, give the exact PowerShell
steps and do not claim you ran them.

Open Blender normally and verify its local listener. Run pipeline.check_mcp,
then verify the Blender tools in this Claude session. Configure the active
scene with --configure-gpu and render the separate smoke scene. Report actual
protocol, Blender version, selected device, image path and any failed step.
Inspect the rendered image. Do not equate configured settings with measured
GPU use or claim Windows/4090 tests that were not performed.

Once the connection works, start new Blender work when I describe the scene.
Use docs/REPOSITORIES.md to choose relevant character, rigging, motion or VFX
tools instead of rebuilding available capabilities. Clone only what the
task needs, verify its official requirements and keep large dependencies
separate. There are no old assets to migrate. The iPhone mocap test is later.
```

## Troubleshooting and known errors

| Symptom | Action |
| --- | --- |
| uv not found or GUI spawn failure | Reopen PowerShell after installing uv; use the actual absolute executable path. The setup discovers and records it. |
| Wrong Desktop configuration | Use Settings → Developer → Edit Config. Store installations can use a redirected path; --config can select the actual file. |
| Blender is open during apply | Save and close it, then rerun. The script will not stop it or overwrite live preferences. |
| Old package add-on detected | Inspect and disable/remove that old package through Blender before installing a second copy. The setup deliberately stops rather than silently leaving a stale enabled module. |
| No module named blender_mcp | The external server and in-Blender add-on are separate. Check installation directory, enabled add-on and Blender version. |
| Connection refused | Open the normal Blender GUI, enable the add-on and start its listener on 9876. Recheck after loading another file. |
| Starting the listener with blender -b fails | Expected: the upstream add-on requires a GUI event loop. Use -b for rendering jobs, not the live MCP server. |
| Protocol mismatch | Align server and add-on versions; restart both Blender and the client. Do not update just one component from a moving main branch. |
| Another blender server is configured | Inspect the existing entry. --replace-existing explicitly permits replacement and backup; do not use it blindly. |
| Port already used | Identify the intended Blender session. Do not stop unrelated processes or expose the unauthenticated socket publicly. |
| Defender detects the remote PowerShell installer | This workflow uses WinGet and a pinned package instead of the reported website-script command. Do not disable protection to force that command. [Upstream report 401](https://github.com/ahujasid/mcp-for-blender/issues/401) was open when checked. |
| Non-English Windows tasklist decoding error | The inspected pinned helper uses OEM decoding. Avoid copying older examples that decode tasklist with the ANSI default. [Upstream report 380](https://github.com/ahujasid/mcp-for-blender/issues/380) was closed when checked. |
| Claude Code CLI crashes during registration | The setup reports failure and restores the original configuration state. Inspect the native CLI installation and retry its printed registration deliberately. [Report 387](https://github.com/ahujasid/mcp-for-blender/issues/387) concerns a macOS kqueue failure; it is not evidence that every Windows installation has the same problem. |
| OptiX/4090 missing | Check driver and Blender version, then enumerate devices. Do not describe a CPU fallback as a 4090 render. |
| Environment changed after an update | Keep uv.lock and use --frozen. The client uses the same project environment. Rerun setup if the repository moves. |
| Test output already exists | Choose a new empty directory. The smoke test does not overwrite prior work. |

## Sources and verification

Official references used include the upstream package source/distribution, Claude's [MCP documentation](https://code.claude.com/docs/en/mcp), its [Windows setup](https://code.claude.com/docs/en/setup), [MCP local-server guidance](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers), [uv tools](https://docs.astral.sh/uv/concepts/tools/) and Blender/NVIDIA rendering guidance linked above. The code uses the compatible official MCP SDK already required by the pinned package.

Local validation: configuration preservation, conflict refusal, malformed JSON, idempotence, rollback, frozen launch arguments, directory-style add-on rejection, missing-device failure and error-result handling are covered by the Python tests. A real MCP process matched protocol 13 and performed scene inspection and Python execution in a separate Blender 5.2.2 GUI session on macOS. A new CPU smoke scene rendered and its image was inspected. These checks did not resume an old scene.

Not verified on this Mac: native Windows application discovery/configuration, the friend's Claude account policies, actual 4090 OptiX execution and viewport behavior inside that Claude client. CI runs the Python tests on Windows and Linux; a hosted runner is not the target GPU. Run the connection, client-tool and image checks on the Windows PC before considering installation complete.
