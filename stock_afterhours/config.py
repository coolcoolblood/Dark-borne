# -*- coding: utf-8 -*-
"""Configuration management for stock afterhours analysis."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AnalysisConfig:
    """Configuration for afterhours analysis.

    Attributes:
        api_key: EODHD API key
        exchange_code: Exchange code (default: US)
        output_dir: Directory for output files
        min_day_turnover_musd: Minimum full day turnover in millions USD
        min_ah_turnover_musd: Minimum afterhours turnover in millions USD
        min_ah_gain_pct: Minimum afterhours gain percentage
        api_timeout: API request timeout in seconds
        max_retries: Maximum number of retry attempts for API calls
        rate_limit_delay: Delay between API calls in seconds
    """

    api_key: str
    exchange_code: str = "US"
    output_dir: Path = Path.home() / "stock_analysis"
    min_day_turnover_musd: float = 5.0
    min_ah_turnover_musd: float = 1.0
    min_ah_gain_pct: float = 10.0
    api_timeout: int = 20
    max_retries: int = 3
    rate_limit_delay: float = 0.5

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("EODHD_API_KEY is required")

        # Ensure output directory exists
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls, output_dir: Optional[str] = None) -> "AnalysisConfig":
        """Load configuration from environment variables.

        Args:
            output_dir: Optional override for output directory

        Returns:
            AnalysisConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv('EODHD_API_KEY')
        if not api_key:
            raise ValueError(
                "EODHD_API_KEY environment variable is required. "
                "Set it with: export EODHD_API_KEY='your_api_key_here'"
            )

        # Determine output directory
        if output_dir:
            out_dir = Path(output_dir)
        elif os.getenv('OUTPUT_DIR'):
            out_dir = Path(os.getenv('OUTPUT_DIR'))
        else:
            out_dir = Path.home() / "stock_analysis"

        return cls(
            api_key=api_key,
            exchange_code=os.getenv('EXCHANGE_CODE', 'US'),
            output_dir=out_dir,
            min_day_turnover_musd=float(os.getenv('MIN_DAY_TURNOVER', '5.0')),
            min_ah_turnover_musd=float(os.getenv('MIN_AH_TURNOVER', '1.0')),
            min_ah_gain_pct=float(os.getenv('MIN_AH_GAIN', '10.0')),
            api_timeout=int(os.getenv('API_TIMEOUT', '20')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            rate_limit_delay=float(os.getenv('RATE_LIMIT_DELAY', '0.5')),
        )

    def get_output_path(self, analysis_date: str) -> Path:
        """Get output file path for a specific analysis date.

        Args:
            analysis_date: Date string in YYYY-MM-DD format

        Returns:
            Path to output Excel file
        """
        return self.output_dir / f"afterhours_analysis_{analysis_date}.xlsx"
