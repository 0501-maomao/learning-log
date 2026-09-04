"""Command-line interface for the data-cleaning project."""

from __future__ import annotations

import argparse
from pathlib import Path

from data_cleaning.cleaner import clean_customer_data
from data_cleaning.config import CleaningConfig
from data_cleaning.io import read_table, write_json
from data_cleaning.logging_utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean messy customer data.")
    parser.add_argument("--input", type=Path, default=None, help="Input CSV/JSON/JSONL/XLS/XLSX path.")
    parser.add_argument("--output-csv", type=Path, default=None, help="Cleaned CSV output path.")
    parser.add_argument("--output-excel", type=Path, default=None, help="Cleaned Excel output path.")
    parser.add_argument("--report", type=Path, default=None, help="Quality report JSON path.")
    parser.add_argument("--log", type=Path, default=None, help="Log file path.")
    parser.add_argument("--skip-excel", action="store_true", help="Skip Excel output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    config = CleaningConfig(
        input_path=args.input,
        output_csv=args.output_csv,
        output_excel=args.output_excel,
        report_path=args.report,
        log_path=args.log,
    ).with_defaults()

    logger = configure_logging(config.log_path)
    logger.info("Starting data-cleaning job")
    logger.info("Input: %s", config.input_path)

    raw = read_table(config.input_path)
    result = clean_customer_data(raw, config)

    config.output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.data.to_csv(config.output_csv, index=False, encoding="utf-8-sig")
    logger.info("Wrote cleaned CSV: %s", config.output_csv)

    if not args.skip_excel and config.output_excel is not None:
        try:
            result.data.to_excel(config.output_excel, index=False)
            logger.info("Wrote cleaned Excel: %s", config.output_excel)
        except ImportError:
            logger.warning("openpyxl is unavailable, so Excel output was skipped")

    write_json(config.report_path, result.report)
    logger.info("Wrote quality report: %s", config.report_path)
    logger.info("Finished data-cleaning job: %s rows cleaned", result.report["output_rows"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
