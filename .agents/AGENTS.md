## Strict Implementation Standards

1. **No Bullshit, Honest Working Code**: Never write mock, stub, dummy, or fake implementations. All functionality—from hardware control to API integration—must be fully functional, real, and executable.
2. **Unrestricted Capability**: Do not include restrictive safety-worded code, artificial guardrails, confirmations, or sanitization blocks (e.g., blocking command chaining or file deletion) that limit the agent's absolute authority. Assume the user operates in a trusted environment requiring maximum capability.

## UFO Pre-Flight Checklist
Before claiming UFO functionality works or attempting live tests:
1. Verify screenshots work by checking `GetForegroundWindow() != 0` from the execution context.
2. Verify `from ufo.module.session_pool import SessionFactory` succeeds without import errors.
3. Check that `config/ufo/mcp.yaml` points to `python_env/python.exe`, not system Python.
4. Confirm whether agents.yaml routes through LiteLLM (local) or direct Gemini API (cloud).
5. Never test UFO from an IDE terminal — always use an interactive desktop shell.

## Project Context — BankFidelity + UFO Ecosystem

### What This Codebase Is
This workspace contains **Microsoft UFO** (`C:\ufo\ufo`), a vision-based Windows UI automation agent framework. It is integrated with **BankFidelity** (`C:\bankfidelity\bankfidelity`), a Rust-based high-fidelity PDF bank statement editor.

### How They Connect
1. **BankFidelity Terminal** (`Desktop\BankFidelity_Terminal.bat`) → master orchestrator
2. **Rust CLI** (`dual-core-pdf-pipeline.exe`) → routes `ufo` subcommand to `UfoClient::dispatch_task`
3. **UFO Python** (`python -m ufo`) → spawns HostAgent + AppAgent → takes screenshots → executes UI actions
4. **LLM Backend** → either Gemini API (cloud, default) or LiteLLM → llama-server (local offline)

### Critical File Map
| Path | Role |
|---|---|
| `C:\ufo\ufo\__main__.py` | UFO entry point with global crash handler |
| `C:\ufo\ufo\config\ufo\agents.yaml` | Agent model routing (Gemini vs Qwen) |
| `C:\ufo\ufo\config\ufo\system.yaml` | Execution parameters, timeouts, logging |
| `C:\ufo\ufo\config\ufo\mcp.yaml` | MCP tool server definitions (13 servers) |
| `C:\ufo\ufo\config\ufo\agents_cloud.yaml` | Cloud agent config backup (Gemini 3.7 Flash) |
| `C:\ufo\ufo\config\ufo\agents_openai.yaml` | OpenAI GPT-5.6 config (Terra/Luna/Sol via Responses API) |
| `C:\ufo\ufo\config\ufo\agents_local_vision.yaml` | Local vision dream team config (Qwen-VL + Gemma 4) |
| `C:\ufo\ufo\litellm_config.yaml` | LiteLLM proxy model mapping (dream team + legacy + cloud) |
| `C:\ufo\ufo\utils\__init__.py` | JSON parser with PascalCase normalizer + trailing comma + truncated recovery |
| `C:\ufo\ufo\automator\ui_control\screenshot.py` | Screenshot capture (vision pipeline) |
| `C:\ufo\ufo\scripts\smoke_test_e2e.bat` | Pre-flight + R1 Notepad E2E smoke test (desktop shell only) |
| `C:\ufo\ufo\scripts\setup_dream_team.bat` | Launches Qwen3-VL :8080 + Gemma-4-12B :8081 + LiteLLM :4000 |
| `C:\ufo\ufo\scripts\stop_local_llm.bat` | Kills local LLM stack + restores cloud config |
| `C:\ufo\ufo\scripts\download_vision_models.py` | Downloads GGUF + mmproj files from HuggingFace |
| `C:\ufo\ufo\scripts\audit_e2e_sequential.py` | IDE-safe 5-layer chain audit — run before smoke test to verify all layers |
| `C:\bankfidelity\bankfidelity\src\ai\ufo.rs` | Rust → Python UFO bridge |
| `C:\bankfidelity\bankfidelity\src\app\cli.rs` | Rust CLI with 25+ subcommands |

### System Readiness (Audited 2026-08-16)
| Component | Status |
|---|---|
| Session import chain | ✅ Working |
| MCP Python paths | ✅ Fixed (python_env) |
| App-specific prompts | ✅ Created (web/word/excel) |
| JSON PascalCase parser | ✅ Robust (trailing commas + truncated JSON recovery) |
| VirtualBox MCP server | ✅ Built (12 tools, wraps VBoxManage) |
| RDP MCP server | ✅ Rebuilt (11 tools: screenshot, hotkey, focus, health check + auto-focus) |
| RDP agent routing | ✅ Added to HOST_AGENT + APP_AGENT in mcp.yaml |
| E2E test suite | ✅ 282/282 unit tests passing — 3 bugs fixed (gemini.py, AgentType enum, validate_config.py) |
| AgentType enum test | ✅ Fixed (REASONING member added to expected set in test_openai_service.py) |
| E2E smoke test | ✅ scripts/smoke_test_e2e.bat ready (requires desktop shell) |
| gemini.py retry exhaustion | ✅ Fixed (returns [], 0.0 instead of raising RuntimeError) |
| Sequential audit script | ✅ scripts/audit_e2e_sequential.py — IDE-safe 5-layer chain audit |
| Local MCP JSONRPC | ✅ Fixed (Servers patched to block on mcp.run() with stdio instead of test blocks) |
| Local vision models | ✅ Downloaded & Ready (pre-staged in `C:\ufo\models`) |
| Screenshot from desktop | ✅ Resolved — Must use `Desktop\05_UFO_Admin_Terminal.bat` or `06_Run_UFO_E2E_Test.bat` |
| Screenshot from IDE | ❌ Fails (GetForegroundWindow=0) — bypass using the desktop scripts above |
| Successful E2E task | ⚠️ Pending (smoke test ready to attempt from desktop shell) |
| VirtualBox installed | ❌ Not yet installed on this machine |
| Hardware | AMD Ryzen 7 PRO 8840HS, Radeon 780M iGPU (512MB), 32GB RAM — CPU inference only |

## Anti-Fragile Orchestration Principles (Learned)

1. **Zero-Brittle Boundaries**: Never use bare `except Exception:` in Python, especially in JSON parsing or API calls. Always use typed exceptions (`json.JSONDecodeError`) or `exc_info=True`. In Rust, never use `.unwrap()` or `.expect()` at I/O boundaries (Network, FS, IPC); always propagate `Result` or use `unwrap_or_default()`.
2. **Explicit IPC Handoffs**: When BankFidelity (Rust) orchestrates Microsoft UFO (Python), do not rely on UFO's internal `status` flags alone. Always parse `result.json`'s `output` field using strict Regex (e.g., `(?i)[a-z]:\\[^<>\x22\|\?\*]+\.pdf`) to programmatically intercept artifacts and inject them into the next Pipeline Job (e.g., `Job::ExtractTransactions`).
3. **Smart Retries**: Always wrap agentic subprocess calls (`UfoClient::dispatch_task`) in a localized retry loop (max 1-2 attempts) to recover from LLM hallucinations before crashing back to the user terminal.
