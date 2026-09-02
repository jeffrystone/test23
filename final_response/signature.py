from pathlib import Path


def load_signature(path: Path | str) -> str:
    signature_path = Path(path)
    if not signature_path.is_file():
        raise FileNotFoundError(f"Signature file not found: {signature_path}")

    text = signature_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Signature file is empty: {signature_path}")
    return text
