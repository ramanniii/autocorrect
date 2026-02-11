# Local AI Autocorrect (macOS + Ollama)

A lightweight, system-wide AI text correction tool that works in any application.

Press a global hotkey → highlighted text is rewritten using a local LLM → corrected text is pasted back automatically.

Runs fully offline using Ollama.

---

## Features

- Works across all apps (Notes, WhatsApp, browsers, IDEs)
- Fully local (no cloud API calls)
- Fixes spelling and grammar
- Inserts missing words where needed
- Removes accidental duplicate or stray short words
- Preserves original tone and meaning
- Clipboard is restored after paste
- Auto-starts Ollama if not running

---

## Stack

- Python
- Ollama
- Mistral model
- Hammerspoon (global hotkey)
- macOS Automation (System Events)

---

## Project Structure

ai-agents/
  autocorrect/
    rewrite_agent.py

Virtual environment location:

~/ai-agent-autocorrect/

---

## Requirements

- macOS
- Python 3.10+
- Homebrew
- Ollama installed
- Hammerspoon installed
- Accessibility permissions enabled

---

## Installation

### Install Ollama

brew install ollama

Pull the model:

ollama pull mistral

---

### Create Python virtual environment

python3 -m venv ~/ai-agent-autocorrect  
source ~/ai-agent-autocorrect/bin/activate  
pip install requests pyperclip  

---

### Place the script

Put rewrite_agent.py into:

~/ai-agents/autocorrect/

---

### Configure global hotkey (Hammerspoon)

File:

~/.hammerspoon/init.lua

Add:

hs.hotkey.bind({"cmd"}, "/", function()
    hs.task.new("/bin/bash", nil, {
        "-c",
        "~/ai-agent-autocorrect/bin/python ~/ai-agents/autocorrect/rewrite_agent.py"
    }):start()
end)

Reload Hammerspoon:

hs.reload()

---

## Usage

1. Highlight text anywhere  
2. Press Cmd + /  
3. Text is corrected and replaced automatically  

Works in:

- Notes
- Mail
- Browsers
- WhatsApp
- Slack
- Android Studio
- VS Code

---

## How It Works

Hotkey triggers Python script.  
Script copies highlighted text.  
Ollama server auto-starts if not running.  
Model loads in background.  
Text sent to local LLM.  
Corrected result pasted back into the active app.  
Clipboard restored.

---

## Prompt Customisation

Editing rules are defined inside PROMPT_TEMPLATE in rewrite_agent.py.

You can adjust:

- tone strictness
- grammar aggressiveness
- rewrite behaviour
- allowed word insertion

---

## Troubleshooting

Hotkey does nothing:

- Check Hammerspoon Accessibility permission
- Ensure System Events permission enabled

Ollama errors:

Run:

ollama serve

Paste fails:

Enable Automation permissions for:

- Hammerspoon → System Events
- Python → System Events

Model slow first run:

Normal — model loads into RAM on first execution.

---

## Roadmap

- Summarise hotkey
- Professional rewrite mode
- Email tone mode
- Idle model unload
- Android Studio plugin integration
- Background agent mode

---

## License

Personal project / experimental use.
