import json
import logging
import os
from os import PathLike
from pathlib import Path


logger = logging.getLogger(__name__)


def save_json(data: dict, dest_dir: str, filename):
    os.makedirs(dest_dir, exist_ok=True)
    p = f"{dest_dir}/{filename}.json"
    with open(p, "w", encoding="utf-8") as file:
        logger.debug("Dumped '%s' to '%s'", data, p)
        json.dump(data, file, indent=4, ensure_ascii=False)
    return p


def get_keywords(path: PathLike | str) -> list[str]:
    content = Path(path).read_text(encoding="utf-8")
    return [
        kw for kw in content.split("\n") if kw and not kw.startswith(("##", "--"))
    ]
