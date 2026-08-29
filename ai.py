import argparse
import json
from pathlib import Path


def generate(project):
    examples = [item["path"] for item in project.get("files", []) if item.get("path")][:3]
    return {
        "summary": "Готов2 взять задачу. Сначала аудит источников, потом наращивание живого трафика.",
        "days": 7,
        "estimate_cost": 15000,
        "examples": examples,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(generate(project), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
