# -*- coding: utf-8 -*-
"""Command-line interface for stock afterhours analysis."""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

from .config import AnalysisConfig
from .analysis import AfterhourAnalyzer
from .export import export_to_excel, print_summary_statistics


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_header(config: AnalysisConfig) -> None:
    """Print analysis header with configuration.

    Args:
        config: Analysis configuration
    """
    print("=" * 80)
    print("Stock Afterhours Analysis - Version 10.0 (Refactored)")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  Exchange: {config.exchange_code}")
    print(f"  Min Day Turnover: ${config.min_day_turnover_musd}M USD")
    print(f"  Min AH Turnover: ${config.min_ah_turnover_musd}M USD")
    print(f"  Min AH Gain: {config.min_ah_gain_pct}%")
    print(f"  Output Directory: {config.output_dir}")
    print("\nWorkflow:")
    print("  1. Get all stocks EOD data via EODHD API")
    print(f"  2. Filter: Full day turnover > {config.min_day_turnover_musd}M USD")
    print(f"  3. Filter: Afterhours turnover >= {config.min_ah_turnover_musd}M USD (4:01pm-7:59pm EST)")
    print(f"  4. Filter: Afterhours gain >= {config.min_ah_gain_pct}% (vs 4:00pm close)")
    print("  5. Export to Excel with detailed metrics")
    print("\nNext Day Comparison:")
    print("  Next Day High (4:01am-7:59pm) vs Current Day 7:59pm Close")
    print("=" * 80)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Analyze afterhours stock trading activity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single date
  %(prog)s 2025-11-06

  # Analyze with custom output directory
  %(prog)s 2025-11-06 --output-dir /path/to/output

  # Analyze with custom thresholds
  %(prog)s 2025-11-06 --min-turnover 10 --min-ah-gain 15

  # Analyze date range
  %(prog)s --start-date 2025-11-01 --end-date 2025-11-06

  # Enable verbose logging
  %(prog)s 2025-11-06 --verbose

Environment Variables:
  EODHD_API_KEY       EODHD API key (required)
  OUTPUT_DIR          Output directory for Excel files
  EXCHANGE_CODE       Exchange code (default: US)
  MIN_DAY_TURNOVER    Minimum day turnover in M USD (default: 5.0)
  MIN_AH_TURNOVER     Minimum afterhours turnover in M USD (default: 1.0)
  MIN_AH_GAIN         Minimum afterhours gain percentage (default: 10.0)
        """
    )

    parser.add_argument(
        'date',
        nargs='?',
        help='Analysis date in YYYY-MM-DD format (default: 2025-11-06)'
    )

    parser.add_argument(
        '--start-date',
        metavar='DATE',
        help='Start date for date range analysis (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        metavar='DATE',
        help='End date for date range analysis (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--output-dir',
        metavar='PATH',
        help='Output directory for Excel files (overrides OUTPUT_DIR env var)'
    )

    parser.add_argument(
        '--min-turnover',
        type=float,
        metavar='MUSD',
        help='Minimum day turnover in millions USD (overrides MIN_DAY_TURNOVER)'
    )

    parser.add_argument(
        '--min-ah-gain',
        type=float,
        metavar='PCT',
        help='Minimum afterhours gain percentage (overrides MIN_AH_GAIN)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 10.0'
    )

    return parser.parse_args()


def validate_date(date_str: str) -> str:
    """Validate date format.

    Args:
        date_str: Date string to validate

    Returns:
        Validated date string

    Raises:
        ValueError: If date format is invalid
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    args = parse_arguments()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        config = AnalysisConfig.from_env(output_dir=args.output_dir)

        # Override config with command-line arguments
        if args.min_turnover is not None:
            config.min_day_turnover_musd = args.min_turnover
        if args.min_ah_gain is not None:
            config.min_ah_gain_pct = args.min_ah_gain

        # Print header
        print_header(config)

        # Determine date range
        if args.start_date and args.end_date:
            # Date range mode
            start_date = validate_date(args.start_date)
            end_date = validate_date(args.end_date)
            logger.info(f"Analyzing date range: {start_date} to {end_date}")
            output_filename = f"afterhours_analysis_{start_date}_to_{end_date}.xlsx"

        elif args.date:
            # Single date mode
            date = validate_date(args.date)
            start_date = end_date = date
            logger.info(f"Analyzing single date: {date}")
            output_filename = f"afterhours_analysis_{date}.xlsx"

        else:
            # Default date
            date = "2025-11-06"
            start_date = end_date = date
            logger.info(f"Using default date: {date}")
            output_filename = f"afterhours_analysis_{date}.xlsx"

        # Initialize analyzer
        analyzer = AfterhourAnalyzer(config)

        # Run analysis
        print("\nStarting analysis...\n")
        df_results = analyzer.analyze_date_range(start_date, end_date)

        # Export results
        if not df_results.empty:
            output_path = config.output_dir / output_filename
            export_to_excel(df_results, output_path)
            print(f"\nExcel file saved: {output_path}")

            # Print summary statistics
            print_summary_statistics(df_results)

            print(f"\nAnalysis complete!")
        else:
            print("\nNo matching records found")
            print(f"Stocks must meet: {config.min_ah_gain_pct}%+ gain (vs 4PM close) "
                  f"AND {config.min_ah_turnover_musd}M+ USD volume in 4:01pm-7:59pm EST window")

        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
