from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .convert import convert_ibt_to_csv

logger = logging.getLogger("iracing_telemetry")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iracing-telemetry",
        description=(
            "Convert iRacing .ibt telemetry files to CSV and generate an "
            "interactive analysis report."
        ),
    )
    parser.add_argument("input", type=Path, help="Path to a .ibt file")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated files (default: ./csv_output and ./plots)",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot and report generation (CSV export only)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    input_path: Path = args.input
    if not input_path.exists():
        parser.error(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != ".ibt":
        parser.error("Input must be a .ibt file")

    try:
        convert_ibt_to_csv(
            input_path=input_path,
            output_dir=args.output_dir,
            generate_plots=not args.no_plots,
        )
    except Exception as exc:  # noqa: BLE001 - surface any failure as a clean CLI error
        logger.error("Conversion failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
