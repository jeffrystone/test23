from datetime import datetime
from pathlib import Path

from src.final_response.config import FinalResponseEnvs
from src.final_response.greeting import get_time_greeting
from src.final_response.signature import load_signature


def assemble_response(
    llm_text: str,
    *,
    now: datetime | None = None,
    signature_path: Path | str | None = None,
) -> str:
    envs = FinalResponseEnvs()
    path = Path(signature_path) if signature_path is not None else envs.RESPONSE_SIGNATURE_FILE

    parts = [
        get_time_greeting(now=now),
        (llm_text or "").strip(),
        load_signature(path),
    ]
    return "\n\n".join(part for part in parts if part)
