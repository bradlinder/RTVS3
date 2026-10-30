# Local AI Setup & Autonomous Smart Router Guide

This guide covers setting up offline, privacy-first AI development for the **Radio & TV Story Segmenter** on modern AMD hardware (specifically AMD Ryzen AI 9 HX 370 / Radeon 890M with 64GB RAM and 32GB UMA VRAM).

You can configure everything **automatically via Antigravity** using a single command, or follow the **step-by-step manual instructions** below.

---

## 1. Quick Automated Setup (Recommended for Antigravity)

If you are running Antigravity or an agent with shell access on your machine, simply run:

```bash
# 1. Run the non-destructive automated setup script
python scripts/setup_local_ai.py --all

# 2. Launch the Autonomous Smart Router Proxy in the background
python scripts/task_router.py --serve-proxy
```

### What This Does Automatically:
1. **Hardware & VRAM Probe**: Verifies AMD Ryzen AI 9 HX 370, Radeon 890M (`gfx1150`), and configures KV-cache memory parameters (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`).
2. **Model Suite Provisioning**: Connects to your local Ollama instance and pulls the tiered model suite:
   * `qwen3.8-27b` (Lead Architect & Refactoring)
   * `qwen3:14b` (Interactive Chat & Debugging)
   * `qwen3.5:9b` (Fast Edits & Small Patches)
   * `qwen2.5-coder:32b` (Surgical Diffs & Deterministic Patches)
   * `qwen2.5-coder:1.5b` (Dedicated sub-50ms Tab Autocomplete)
   * `deepseek-r1:14b` (Concurrency Proofs & Math Logic)
3. **IDE Configuration**:
   * Creates `.continue/config.json` configured with `rtvs-smart-router` as the primary chat endpoint and `qwen2.5-coder:1.5b` for tab autocomplete.
   * Creates `.vscode/settings.json` with Python analysis and search exclusions.
   * Generates `.clinerules` and `.cursorrules` with token-thrift and symbol-first reading rules.
4. **Starts Smart Router**: Binds `http://127.0.0.1:8000/v1`, enabling natural language task dispatching without memorizing slash commands.

---

## 2. Step-by-Step Manual Setup

If you prefer to configure Ollama, VS Code, Continue, and Cline manually, follow these instructions.

### Step 2.1: Install and Configure Ollama
1. **Download Ollama**:
   * Windows: Download and run the installer from [ollama.com/download/windows](https://ollama.com/download/windows).
   * Linux: Run `curl -fsSL https://ollama.com/install.sh | sh`.
2. **Set Environment Variables for AMD Strix Point (Radeon 890M / Vulkan / ROCm)**:
   * **Windows (PowerShell)**:
     ```powershell
     [System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "1", "User")
     [System.Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE", "q8_0", "User")
     [System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "1", "User")
     [System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "127.0.0.1:11434", "User")
     ```
   * **Linux (`~/.bashrc` or systemd service)**:
     ```bash
     export OLLAMA_FLASH_ATTENTION=1
     export OLLAMA_KV_CACHE_TYPE=q8_0
     export OLLAMA_NUM_PARALLEL=1
     export OLLAMA_HOST=127.0.0.1:11434
     ```
3. **Pull the Tiered Local Models**:
   Open a terminal and run:
   ```bash
   # Primary Refactoring & Architecture (262k context, DeltaNet linear attention)
   ollama pull qwen3.8-27b

   # Interactive Chat & Fast Debugging (~11-13 tok/s)
   ollama pull qwen3:14b

   # Rapid Edits & Small Patches (~16-18 tok/s)
   ollama pull qwen3.5:9b

   # Surgical Diffs & Zero-Fluff Deterministic Patches
   ollama pull qwen2.5-coder:32b

   # Instant Tab Autocomplete (FIM, sub-50ms latency)
   ollama pull qwen2.5-coder:1.5b

   # Deep Concurrency Proofs & Race Condition Audits
   ollama pull deepseek-r1:14b
   ```

---

### Step 2.2: Launch the Autonomous Smart Router Proxy
The proxy listens as an OpenAI-compatible server on `http://127.0.0.1:8000/v1` and translates natural language queries into the best local model:

```bash
# In your terminal or a dedicated terminal tab:
python scripts/task_router.py --serve-proxy
```

You will see:
```text
=================================================================
 RTVS AUTONOMOUS SMART ROUTING PROXY ACTIVE
=================================================================
 Listening on:     http://127.0.0.1:8000/v1
 Forwarding to:    http://127.0.0.1:11434
 Unified Endpoint: 'rtvs-smart-router' (automatic natural language dispatch)
 Targets:          Qwen3.8-27B | Qwen3:14B | Qwen2.5-Coder:32B | DeepSeek-R1
=================================================================
```

---

### Step 2.3: Configure VS Code with Continue

1. Install the **Continue** extension from the VS Code Marketplace.
2. Open `~/.continue/config.json` (or `.continue/config.json` in your workspace root) and paste:

```json
{
  "models": [
    {
      "title": "Smart Router (Autonomous NL Dispatcher)",
      "provider": "openai",
      "model": "rtvs-smart-router",
      "apiBase": "http://127.0.0.1:8000/v1",
      "apiKey": "local-no-key"
    },
    {
      "title": "Lead Architect (Qwen 3.8 27B Direct)",
      "provider": "ollama",
      "model": "qwen3.8-27b",
      "apiBase": "http://127.0.0.1:11434"
    },
    {
      "title": "Fast Chat & Debug (Qwen 3 14B Direct)",
      "provider": "ollama",
      "model": "qwen3:14b",
      "apiBase": "http://127.0.0.1:11434"
    },
    {
      "title": "Surgical Diff & Patch (Qwen 2.5 Coder 32B Direct)",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "apiBase": "http://127.0.0.1:11434"
    },
    {
      "title": "Deep Reasoning & Concurrency (R1 14B Direct)",
      "provider": "ollama",
      "model": "deepseek-r1:14b",
      "apiBase": "http://127.0.0.1:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Autocomplete (Qwen 1.5B FIM)",
    "provider": "ollama",
    "model": "qwen2.5-coder:1.5b",
    "apiBase": "http://127.0.0.1:11434"
  }
}
```

Now, **Continue will automatically use `rtvs-smart-router` as your default chat model** and **`qwen2.5-coder:1.5b` for keystroke tab-autocomplete**.

---

### Step 2.4: Configure Cline / Roo Code (Optional Alternative)

If using **Cline** or **Roo Code**:
1. Open the Cline settings gear icon.
2. Select **API Provider**: `OpenAI-Compatible`.
3. Set **Base URL**: `http://127.0.0.1:8000/v1`
4. Set **API Key**: `local-no-key` (any text).
5. Set **Model ID**: `rtvs-smart-router`
6. Cline will now route all agentic coding tasks through the smart proxy automatically.

---

## 3. How Natural Language Dispatching Works

You do not need to memorize any slash commands or switch dropdowns. The proxy inspects your prompt and context:

* **Refactoring & Monoliths**: *"Decompose `audio_normalization.py` into separate DSP engine and worker files"* $\rightarrow$ Dispatches to **`Qwen3.8-27B`** (large context, multi-file reasoning).
* **Targeted Diffs**: *"Replace the error handling on line 45 with a graceful None check. Just give me the fix."* $\rightarrow$ Dispatches to **`Qwen2.5-Coder:32B`** (zero chatter, exact contiguous diff).
* **Interactive Q&A**: *"What does `QSettings.sync()` do in PyQt6?"* $\rightarrow$ Dispatches to **`Qwen3:14B`** (fast conversational response).
* **Race Conditions & Threading**: *"Analyze `inline_speaker_rename` for race conditions during background sync"* $\rightarrow$ Dispatches to **`DeepSeek-R1:14B`** (step-by-step deductive chain of thought).
* **Typing in Editor**: Type code $\rightarrow$ **`Qwen2.5-Coder:1.5B`** suggests ghost-text inline completions in <50ms.
