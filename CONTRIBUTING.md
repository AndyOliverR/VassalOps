# 🤝 Contributing to VassalOps

Thank you for checking out VassalOps! We are building a local-first, self-improving workspace, and we love community contributions. Whether you are fixing an indentation bug, optimizing context window sizes, or adding a new theme to the interface, your help makes a huge difference.

---

## 📂 Project Directory Map
To help you find your way around the codebase quickly:
- `app.py`: The core application entry point, Win32 window hooks, and pywebview UI bridge routes.
- `src/execution/`: Contains the primary automation scripts (`macro_player.py`, `macro_recorder.py`, `macro_orchestrator.py`).
- `src/execution/mcp_server.py`: The Model Context Protocol (MCP) server environment hosting decoupled tools.
- `src/execution/diagnostics_engine.py`: The multi-agent Screener/Verifier trace log processing module.
- `storage/dashboard/`: Frontend minimalist template framework (HTML, CSS layout, JavaScript streams).

---

## 🚀 Active Roadmap: Good First Issues
If you want to contribute but are not sure where to start, we have pre-triaged 3 actionable features. Pick one, open a GitHub Issue to claim it, and submit your Pull Request!

### 1. [Good First Issue] Add More Synthetic Tasks to IssueBench
- **File:** `src/execution/issue_bench.py`
- **Goal:** Expand our synthetic task benchmark library. Add 3 new mock error profiles (e.g., Clipboard parsing mismatch, voice-ledger synthesis timeout, or disk write denial exceptions) into the JSON array generator to stress-test the verifier sub-agent boundaries.

### 2. [Good First Issue] Add a Dark/Light Mode Theme Toggle UI
- **File:** `storage/dashboard/index.html`
- **Goal:** Improve the customization settings panel drawer by adding a visual theme toggle slider or button mechanism. Bind it to local browser memory cache (`localStorage`) so user theme preferences persist perfectly across window lifecycle boots.

### 3. [Good First Issue] Expand the MCP Server with a System Disk Space Tool
- **File:** `src/execution/mcp_server.py`
- **Goal:** Enhance our universal tool router. Wrap a native Python filesystem check function into the tool layout array so the main agent loop can autonomously check available hard drive storage allocation blocks during background optimization loops.

---

## 🛠️ Contribution Workflow
1. Fork the repository and create your feature branch: `git checkout -b feature/amazing-improvement`
2. Ensure your Python files compile perfectly without formatting or indentation errors: `python -m py_compile path/to/file.py`
3. Commit your modifications with a crisp descriptive log message.
4. Push to your branch and open a clean Pull Request against the `main` branch.

We review every single PR rapidly. Let's build the ultimate local desktop agent framework together!