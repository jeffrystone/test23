from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "response_prompt.txt"


def load_response_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")
