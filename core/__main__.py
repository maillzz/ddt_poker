"""CLI: python -m core input.json [output.json]."""
import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from core.schemas import PokerParams
from core.solver import run


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m core", description="Оценка покерной раздачи методом Монте-Карло.",
    )
    parser.add_argument("input", type=Path, help="JSON-файл с параметрами раздачи")
    parser.add_argument("output", type=Path, nargs="?", help="JSON-файл результата (по умолчанию — экран)")
    args = parser.parse_args(argv)
    try:
        params = PokerParams.model_validate_json(args.input.read_text(encoding="utf-8"))
        result = run(params.model_dump())
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
    except ValidationError:
        print("Ошибка: проверьте параметры раздачи в JSON-файле.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — граница CLI
        print(f"Ошибка расчёта: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
