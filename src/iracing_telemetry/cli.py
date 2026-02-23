from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .convert import convert_ibt_to_csv


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iracing-telemetry",
        description="Convert iRacing .ibt telemetry files into CSV.",
    )
    parser.add_argument("input", type=Path, help="Path to a .ibt file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: <input>.csv)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_path: Path = args.input
    if not input_path.exists():
        parser.error(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != ".ibt":
        parser.error("Input must be a .ibt file")

    output_path: Path | None = args.output

    try:
        convert_ibt_to_csv(input_path=input_path, output_path=output_path)
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
