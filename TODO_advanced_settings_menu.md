# TODO: Advanced Settings Menu Implementation Plan

## Objective
Create a fully adjustable "Advanced Settings" interface within the main menu system (e.g., BankFidelity Terminal or Rust CLI) to allow users to modify critical configuration files for BankFidelity and UFO on the fly without manually editing text files.

## Target Configuration Files
1. `C:\bankfidelity\bankfidelity\.env` (API Keys: Mistral, DocAI, Gemini, LlamaParse, etc.)
2. `C:\ufo\ufo\config\ufo\agents.yaml` (AI Model assignments for UFO agents)
3. `C:\ufo\ufo\config\ufo\system.yaml` (UFO execution parameters: timeouts, steps, logging levels)

---

## Execution Plan — STATUS: ALL COMPLETED ✅

### Phase 1: Menu UI & Routing Integration
- [x] **Menu Option Addition**: Added Option `[9]` "Advanced Settings & Master Config Dashboard" to `terminal.py` main menu.
- [x] **Sub-menu Navigation**: Created interactive TUI sub-menus with 4 distinct categories:
  - `1.` API Keys (.env)
  - `2.` UFO Agent Models (agents.yaml)
  - `3.` UFO System Configuration (system.yaml)
  - `4.` Local AI Services Status & Hot-Reload
- [x] **Back/Exit Handling**: Clean zero-key navigation (`[0] Back / Return`) across all nested menus.

### Phase 2: BankFidelity API Keys (.env) Editor
- [x] **Parser Implementation**: Built secure parser with `mask_key()` (`AQ.Ab8...JmQ`) to prevent shoulder surfing while displaying key length and status.
- [x] **Modification Logic**:
  - Implemented updates for `MISTRAL_API_KEY`, `DOCAI_API_KEY`, `GEMINI_API_KEY`, `LLAMAPARSE_API_KEY`, `PDFREST_API_KEY`, `APPLITOOLS_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, and custom keys.
  - Validated input with rollback protection.
- [x] **Save Mechanism**: Atomic writes to `.env` using `.env.tmp` with automatic `.env.bak` backups while preserving all comments and surrounding keys.

### Phase 3: UFO Agent Models (agents.yaml) Editor
- [x] **Parser Implementation**: Robust PyYAML loader for `agents.yaml`.
- [x] **Modification Logic**:
  - Displays live configuration for `HOST_AGENT`, `APP_AGENT`, `BACKUP_AGENT`, `EVALUATION_AGENT`.
  - Built 3 one-shot presets: Gemini 3.7 Flash Cloud, OpenAI GPT-4o, Local Vision Dream Team (:4000).
  - Built custom agent model / endpoint editor.
- [x] **Save Mechanism**: Validates YAML structure before saving with `.yaml.bak` rollback protection.

### Phase 4: UFO System Configuration (system.yaml) Editor
- [x] **Parser Implementation**: PyYAML loader for `system.yaml`.
- [x] **Modification Logic**:
  - Adjust numerical tunables: `MAX_STEP`, `MAX_ROUND`, `TIMEOUT`, `MAX_RETRY`, `MAX_TOKENS`, `TEMPERATURE`, `SLEEP_TIME`, `AFTER_CLICK_WAIT`.
  - Toggle boolean parameters: `VISUAL_MODE`, `PRINT_LOG`.
  - Enforces type safety (int/float/bool) during interactive editing.
- [x] **Save Mechanism**: Atomic write with `.yaml.bak` backup.

### Phase 5: Hot-Reloading & State Management
- [x] **On-the-Fly Application**: Direct integration with `backend_state.json` and agent reload triggers.
- [x] **Service Restart Logic**: Integrated restart triggers for `setup_dream_team.bat` and `stop_local_llm.bat` with live health probing on ports `:4000`, `:8080`, `:8081`.
- [x] **Validation & Error Handling**: Automated self-test command (`python scripts/advanced_settings.py --test`) and graceful exception handlers on all file operations.
- [x] **Desktop Launcher Integration**: Upgraded `Desktop\scripts\07_Configuration_Dashboard.bat` to launch the interactive dashboard directly.
