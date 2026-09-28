from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .convert import convert_batch, iter_ibt_files

logger = logging.getLogger("iracing_telemetry")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iracing-telemetry",
        description=(
            "Convert iRacing .ibt telemetry files to CSV and generate an "
            "interactive analysis report."
        ),
    )
    parser.add_argument(
        "input", type=Path, help="A .ibt file or a directory of .ibt files"
    )
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
        help="Skip report generation (CSV export only)",
    )
    parser.add_argument(
        "--units",
        choices=["mph", "kph"],
        default="mph",
        help="Speed units for the report (default: mph)",
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
        parser.error(f"Input not found: {input_path}")

    if input_path.is_file() and input_path.suffix.lower() != ".ibt":
        parser.error("Input file must be a .ibt file")

    files = iter_ibt_files(input_path)
    if not files:
        parser.error(f"No .ibt files found in {input_path}")

    results = convert_batch(
        files,
        output_dir=args.output_dir,
        generate_plots=not args.no_plots,
        units=args.units,
    )

    failures = [path for path, exc in results.items() if exc is not None]
    if len(files) > 1:
        logger.info("Processed %d file(s), %d failed", len(files), len(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
