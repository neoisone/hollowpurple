# Blender workflow

Read README.md first. This repository provides a reusable Windows setup for new Blender work. It contains no old scene assets and does not require them.

- Use the existing mcp-for-blender==2.1.9 package and matching protocol-13 add-on. Use `uv sync --frozen --python 3.11` and `uv run --frozen` from this repository root. Do not redesign the bridge or install every optional research dependency.
- Use native Windows. The client launches the MCP stdio process; the add-on runs inside the normal Blender GUI and listens locally on localhost:9876. Background Blender is for independent renders, not the live MCP listener.
- Run `pipeline.setup_windows` in inspection mode before `--apply`. Preserve unrelated client settings. Stop on config conflicts and show the actual conflicting entry rather than replacing it silently. Do not stop unrelated processes or disable antivirus/firewall protection to work around installation errors.
- Verify tools with `pipeline.check_mcp` or get_addon_status, get_scene_info and a small execute_blender_code call. Report actual results. Do not claim Blender was inspected if no tool ran.
- Select Cycles, OptiX and the RTX 4090. `pipeline.check_mcp --configure-gpu` configures the active scene. `pipeline.configure_gpu.configure` is the shared render configuration. Never silently fall back to CPU. Device settings alone do not prove measured GPU use.
- Inspect scene and add-on status before changing an existing scene. Save a checkpoint before substantial edits. Full builders that reset Blender data belong in separate background processes. Work in small visible steps and use look to inspect viewport, camera and image results.
- Look shader nodes up by type, inspect actual Blender API sockets/enums when uncertain, and apply material colors to shader inputs. Avoid assumptions about older Blender APIs.
- Follow docs/REPOSITORIES.md when selecting characters, rigging, motion or effects. Read the selected repository's official instructions, license and supported versions first. Prefer a direct asset or algorithm reuse over rebuilding the same capability. A repository clone is not proof that its add-on or model works on this machine.
- Start with a short motion/quality preview before a full animation. Use frame sequences for expensive renders. Check noise, glass, reflections, intersections and timing in rendered frames. Keep brightness restrained when requested.
- For iPhone motion capture, use the recorded-video workflow described in the repository guide; it is optional and was deferred. Do not start that test as part of MCP setup.
- Keep new scenes in projects/ and renders in runtime/ or renders/. These are local and ignored by Git. Do not publish user footage, assets, credentials or new GitHub changes without a direct request.
- Use docs/CLAUDE_HANDOFF.md for known errors and source links. State what was tested and what was not. Do not spend model turns rediscovering a setup step already implemented here.
