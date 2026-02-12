import requests
import pyperclip
import subprocess
import time
import re

from pathlib import Path

LAST_USED_FILE = Path.home() / ".ollama_last_used"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral:instruct"
OLLAMA_BIN = "/opt/homebrew/bin/ollama"


# -------------------------
# MODE LOADING FROM FILE
# -------------------------
def get_mode():
    mode_file = Path.home() / ".autocorrect_mode"
    try:
        return mode_file.read_text().strip()
    except:
        return "technical"


def get_mode_rules(mode):
    if mode == "technical":
        return """
MODE: TECHNICAL WRITING
- Preserve developer abbreviations.
- Do NOT expand: env, prod, repo, var, config, auth, db, api, ui.
- Treat them as intentional words.
- Minimal edits preferred.
"""
    elif mode == "casual":
        return """
MODE: CASUAL CHAT
- Preserve slang and informal tone.
- Allow: lol, idk, omg, ahaha.
- Fix spelling and obvious grammar only.
- Do NOT formalise.
"""
    elif mode == "formal":
        return """
MODE: FORMAL WRITING
- Remove slang.
- Expand abbreviations where appropriate.
- Use professional tone.
- Structured sentences preferred.
"""
    else:
        return ""


PROMPT_TEMPLATE = """
SYSTEM ROLE:

You are not a chatbot.
You are not an assistant.

You are a silent text repair engine.

Your only function is to transform input text into corrected text.

You must NEVER:
- explain anything
- describe changes
- comment on the text
- say "no change"
- say "already correct"
- say "already formal"
- justify edits
- respond conversationally
- add labels or headings

If the input is already correct and natural, output exactly:
<<NO_CHANGE>>

{}

STRICT BEHAVIOUR MODES:

1) SINGLE WORD INPUT:
- Only fix spelling.
- Do NOT change casing.
- Do NOT capitalise the first letter.
- Do NOT add punctuation.
- Output exactly one word OR <<NO_CHANGE>>.

2) MULTIPLE WORD INPUT:
- Fix spelling.
- Fix grammar.
- Insert missing words if needed.
- Remove accidental extra words.
- Remove repeated short words if they do not belong.
- Preserve original meaning.
- Preserve tone.
- Perform minimal edits when possible.
- If no changes are needed, output <<NO_CHANGE>>.

TECHNICAL TERMS:
- Do NOT expand abbreviations commonly used in software/dev contexts.
- Preserve terms like: env, prod, repo, var, config, auth, db, api, ui.
- Treat them as intentional and correct words.

FINAL OUTPUT CONTRACT (CRITICAL):

You must output ONLY ONE of the following:

1) The corrected text
2) <<NO_CHANGE>>

Nothing else is permitted.

No explanations.
No commentary.
No meta language.
No reasoning.
No additional sentences.
No formatting.
No labels.

If you output anything outside this contract, the result is invalid.

INPUT:
{}
OUTPUT:
"""




def is_model_running():
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
    subprocess.Popen(
        [OLLAMA_BIN, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    for _ in range(60):
        try:
            requests.get("http://localhost:11434")
            break
        except:
            time.sleep(0.25)

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
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]


def correct_sentence(sentence):
    mode = get_mode()
    prompt = PROMPT_TEMPLATE.format(get_mode_rules(mode), sentence)

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


def rewrite_text():
    mode = get_mode()
    print(f"REWRITE TRIGGERED [{mode}]")

    try:
        previous_clipboard = pyperclip.paste()

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

        ensure_model_ready()

        LAST_USED_FILE.write_text(str(time.time()))

        sentences = split_sentences(original_text)

        corrected_sentences = []
        any_changes = False

        for sentence in sentences:
            corrected, changed = correct_sentence(sentence)
            corrected_sentences.append(corrected)
            if changed:
                any_changes = True

        rewritten = " ".join(corrected_sentences)

        if not any_changes:
            rewritten = original_text

        pyperclip.copy(rewritten)

        time.sleep(0.6)

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

        time.sleep(0.8)

        pyperclip.copy(previous_clipboard)

    except Exception as e:
        print("Rewrite failed:", e)


if __name__ == "__main__":
    rewrite_text()