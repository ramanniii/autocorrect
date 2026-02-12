import requests
import pyperclip
import subprocess
import time
import re

from pathlib import Path

LAST_USED_FILE = Path.home() / ".ollama_last_used"

OLLAMA_URL = "http://localhost:11434/api/generate"
#MODEL = "mistral"
MODEL = "mistral:instruct"
OLLAMA_BIN = "/opt/homebrew/bin/ollama"

PROMPT_TEMPLATE = """
You are a text repair tool.

If the input is already correct and natural, output exactly:
<<NO_CHANGE>>

STRICT BEHAVIOUR MODES:

1) If the input is a SINGLE WORD:
- Only fix spelling.
- Do NOT change casing.
- Do NOT capitalise the first letter.
- Do NOT add punctuation.
- Output exactly one word OR <<NO_CHANGE>>.

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
- If no changes are needed, output <<NO_CHANGE>>.

GLOBAL RULES:
- Output ONLY the corrected text OR <<NO_CHANGE>>.
- No commentary.
- No extra formatting.

TECHNICAL TERMS:
- Do NOT expand abbreviations commonly used in software/dev contexts.
- Preserve terms like: env, prod, repo, var, config, auth, db, api, ui.
- Treat them as correct words.
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

def split_sentences(text):
    """
    Splits text into sentences while preserving punctuation.
    Simple, fast, good enough for autocorrect stage.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]

def correct_sentence(sentence):
    prompt = PROMPT_TEMPLATE.format(sentence)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )

    rewritten = response.json().get("response", "").strip()

    if rewritten == "<<NO_CHANGE>>" or not rewritten:
        return sentence, False
    else:
        return rewritten, True

def classify_sentence(sentence):
    words = sentence.split()

    # single word
    if len(words) == 1:
        return "spelling"

    # many typos / broken structure indicators
    if (
        sentence.islower()
        and "." not in sentence
        and "," not in sentence
        and len(words) > 6
    ):
        return "rewrite"

    # default path
    return "grammar"
    
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
        text_stripped = original_text.strip()
        is_single_word = len(text_stripped.split()) == 1

        if not original_text or not original_text.strip():
            print("No text selected.")
            return

        # Ensure model is running BEFORE sending request
        ensure_model_ready()

        # Update last used timestamp
        LAST_USED_FILE.write_text(str(time.time()))

        sentences = split_sentences(original_text)

        corrected_sentences = []
        any_changes = False

        for sentence in sentences:
            corrected, changed = correct_sentence(sentence)
            corrected_sentences.append(corrected)
            if changed:
                any_changes = True

        # rebuild paragraph
        rewritten = " ".join(corrected_sentences)

        if not any_changes:
            print("NO_CHANGE")
            rewritten = original_text
        else:
            print("CHANGED")

                # Model says "no changes needed" -> paste original text back
        if rewritten == "<<NO_CHANGE>>":
                    print("NO_CHANGE")
                    rewritten = original_text
        else:
            # Optional safety: if the model returns empty for any reason, don't clobber text
            if not rewritten.strip():
                rewritten = original_text

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