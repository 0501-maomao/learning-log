"""Configuration objects for the cleaning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CleaningConfig:
    """Runtime settings for customer data cleaning."""

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    input_path: Path | None = None
    output_csv: Path | None = None
    output_excel: Path | None = None
    report_path: Path | None = None
    log_path: Path | None = None
    min_age: int = 18
    max_age: int = 120

    def with_defaults(self) -> "CleaningConfig":
        """Fill path defaults relative to the project root."""

        input_path = self.input_path or self.project_root / "data" / "raw" / "dirty_customers.csv"
        output_csv = self.output_csv or self.project_root / "data" / "processed" / "cleaned_customers.csv"
        output_excel = self.output_excel or self.project_root / "data" / "processed" / "cleaned_customers.xlsx"
        report_path = self.report_path or self.project_root / "reports" / "quality_report.json"
        log_path = self.log_path or self.project_root / "logs" / "data_cleaning.log"

        return CleaningConfig(
            project_root=self.project_root,
            input_path=input_path,
            output_csv=output_csv,
            output_excel=output_excel,
            report_path=report_path,
            log_path=log_path,
            min_age=self.min_age,
            max_age=self.max_age,
        )
