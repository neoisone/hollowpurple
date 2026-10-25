# Hollowpurple

Set up **Blender MCP → Claude → Cycles OptiX on an RTX 4090**, on native Windows. Start new Blender work without transferring old scenes or assets.

The server is the existing [MCP for Blender](https://github.com/ahujasid/mcp-for-blender) package, pinned to **2.1.9**, with its matching **protocol 13** add-on. The Python scripts reuse its installer and Windows discovery helpers. They do not implement another MCP bridge.

## Windows quickstart

Install Blender **5.2** from [Blender](https://www.blender.org/download/) and a compatible NVIDIA driver. Open Blender once, finish any settings migration, then save and close it. Install Claude Desktop or Claude Code and complete sign-in.

In **PowerShell**, install uv and Git if missing:

```powershell
winget install --id astral-sh.uv -e
winget install --id Git.Git -e
```

Reopen PowerShell. Clone this private repository using an account with access, then run from its root:

```powershell
git clone https://github.com/neoisone/hollowpurple.git
cd hollowpurple
uv sync --frozen --python 3.11

# Inspect first; no settings or add-on files are written.
uv run --frozen python -m pipeline.setup_windows --client desktop

# Close Claude Desktop before applying its config.
uv run --frozen python -m pipeline.setup_windows --client desktop --apply
```

For Claude Code, use `--client code` instead. If needed, install it with `winget install --id Anthropic.ClaudeCode -e`, reopen PowerShell and sign in first. Choose one active client for a Blender session.

If discovery misses Blender, add its **actual** executable path to both setup commands:

```powershell
uv run --frozen python -m pipeline.setup_windows --client desktop --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --apply
```

The installer backs up changed configuration, preserves unrelated servers and refuses to replace a different `blender` entry unless `--replace-existing` is supplied deliberately. A non-5.2 Blender version requires `--allow-version-mismatch` and compatibility checks.

## Verify the connection and GPU

Open **Blender with its normal GUI**. Confirm MCP for Blender is enabled in Preferences and its sidebar listener is running on port **9876**. Fully restart the selected Claude client.

```powershell
# Real MCP handshake, scene read and Python execution; no LLM tokens required.
uv run --frozen python -m pipeline.check_mcp

# Also configure the active live Blender scene for the RTX 4090 through OptiX.
uv run --frozen python -m pipeline.check_mcp --configure-gpu
```

The MCP listener requires Blender's GUI event loop. A separate background Blender is appropriate for rendering, not for hosting this add-on's live MCP connection.

Render a newly generated test scene in a separate process. Use a new empty output directory each time:

```powershell
$BlenderExe = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $BlenderExe --background --python-exit-code 1 --python "$PWD\pipeline\smoke_scene.py" -- --output "$PWD\runtime\smoke-4090"
```

The default requires an **OptiX device named 4090** and fails if absent. It writes `smoke.png`, `mcp_smoke.blend` and `report.json`. Open the image and check GPU activity during rendering. CPU mode exists only as an explicit `--backend CPU` test choice; it is never an automatic fallback.

## Claude instructions and optional repositories

- [Detailed handoff](docs/CLAUDE_HANDOFF.md): architecture, commands, errors, official sources and verification limits.
- [Repository guide](docs/REPOSITORIES.md): all 11 previously selected repositories, their roles, compatibility constraints and when Claude should use them.
- [Recorded repository commits](docs/repositories.json): exact historical references; nothing is cloned automatically.
- [CLAUDE.md](CLAUDE.md): concise working instructions for this repository.

No prior Blender assets, videos, model weights, research environments or Git LFS objects are included. Optional dependencies are selected per task after the core connection works.

## Checks

```powershell
uv run --frozen python -m unittest discover -s tests -v
```

The configuration tests, a real protocol-13 MCP connection to an isolated GUI Blender 5.2.2 session, and a CPU smoke render were checked on macOS. Native Windows installation, Claude's account policies, the actual RTX 4090 and viewport display still need verification on the target PC. CI checks the Python tests on Windows and Linux; it does not have the 4090.
