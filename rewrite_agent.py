import requests
import pyperclip
import subprocess
import time

from pathlib import Path

LAST_USED_FILE = Path.home() / ".ollama_last_used"

OLLAMA_URL = "http://localhost:11434/api/generate"
#MODEL = "mistral"
MODEL = "mistral:instruct"
OLLAMA_BIN = "/opt/homebrew/bin/ollama"

PROMPT_TEMPLATE = """
YYou are a text repair tool.

Correct the input text so it reads like something a person meant to type.

STRICT BEHAVIOUR MODES:

1) If the input is a SINGLE WORD:
- Only fix spelling.
- Do NOT change casing.
- Do NOT capitalise the first letter.
- Do NOT add punctuation.
- Output exactly one word.

2) If the input is MULTIPLE WORDS:
- Fix spelling.
- Fix grammar.
- Insert missing words if needed.
- Remove accidental extra words.
- Remove repeated short words (I, a, and, you, me, etc.) if they do not belong.
- Preserve the original meaning.
- Preserve tone.
- Do NOT respond conversationally.
- Do NOT explain anything.

GLOBAL RULES:
- Output ONLY the corrected sentence, paragraph, or word.
- No commentary.
- No extra formatting.

INPUT:
{}
OUTPUT:
"""


def is_model_running():
    """Check if the Ollama model is currently loaded."""
    try:
        result = subprocess.run(
            [OLLAMA_BIN, "ps"],
            capture_output=True,
            text=True
        )
        return MODEL in result.stdout
    except Exception as e:
        print("Model check failed:", e)
        return False


def start_model():
    """Start Ollama server and warm the model (non-interactive)."""
    print("Starting Ollama server...")

    subprocess.Popen(
        [OLLAMA_BIN, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait until server responds
    for _ in range(60):
        try:
            requests.get("http://localhost:11434")
            break
        except:
            time.sleep(0.25)

    print("Server ready. Ensuring model loaded...")

    # Warm model through API (avoids interactive 'ollama run')
    try:
        requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": "ready",
                "stream": False
            },
            timeout=30
        )
    except:
        pass


def ensure_model_ready():
    if not is_model_running():
        start_model()


def rewrite_text():
    print("REWRITE TRIGGERED")

    try:
        # Save clipboard BEFORE we modify anything
        previous_clipboard = pyperclip.paste()

        # Copy highlighted text
        subprocess.run([
            "osascript",
            "-e",
            'tell application "System Events" to keystroke "c" using command down'
        ])

        time.sleep(0.35)

        original_text = pyperclip.paste()

        if not original_text or not original_text.strip():
            print("No text selected.")
            return

        # Ensure model is running BEFORE sending request
        ensure_model_ready()

        # Update last used timestamp
        LAST_USED_FILE.write_text(str(time.time()))

        prompt = PROMPT_TEMPLATE.format(original_text)

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        rewritten = response.json()["response"].strip()

        # Put rewritten text on clipboard
        pyperclip.copy(rewritten)

        # Give macOS time to register clipboard change
        time.sleep(0.6)

        # Paste into the frontmost application
        subprocess.run([
            "osascript",
            "-e",
            '''
            tell application "System Events"
                tell (first process whose frontmost is true)
                    keystroke "v" using command down
                end tell
            end tell
            '''
        ])

        # Allow paste to complete BEFORE restoring clipboard
        time.sleep(0.8)

        # Restore user's previous clipboard content
        pyperclip.copy(previous_clipboard)

    except Exception as e:
        print("Rewrite failed:", e)


if __name__ == "__main__":
    rewrite_text()