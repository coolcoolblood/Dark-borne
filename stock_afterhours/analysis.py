# -*- coding: utf-8 -*-
"""Core analysis logic for stock afterhours trading."""

import logging
import time
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd

from .config import AnalysisConfig
from .api_client import EODHDClient
from .data_processing import (
    prepare_daily_data,
    check_afterhours_conditions,
    get_next_day_high
)

logger = logging.getLogger(__name__)


class AfterhourAnalyzer:
    """Analyzer for afterhours stock trading activity.

    Attributes:
        config: Analysis configuration
        client: EODHD API client
    """

    def __init__(self, config: AnalysisConfig):
        """Initialize analyzer.

        Args:
            config: Analysis configuration
        """
        self.config = config
        self.client = EODHDClient(config)

    def analyze_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Analyze afterhours trading for a specific date.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            List of analysis results for stocks meeting criteria
        """
        logger.info(f"Analyzing date: {date_str}")

        # Validate trading day
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        if date_obj.weekday() >= 5:
            logger.info(f"Skipped: {date_str} is a weekend")
            return []

        try:
            if not self.client.is_trading_day(date_str):
                logger.info(f"Skipped: {date_str} is not a trading day")
                return []
        except Exception as e:
            logger.error(f"Error checking trading day: {e}")
            return []

        # Fetch today's data
        try:
            df_today = self.client.fetch_eod_data(date_str)
            if df_today is None or df_today.empty:
                logger.warning(f"No data available for {date_str}")
                return []
        except Exception as e:
            logger.error(f"Error fetching today's data: {e}")
            return []

        # Get previous trading day and fetch its data
        try:
            prev_date = self.client.get_previous_trading_day(date_str)
            if not prev_date:
                logger.warning(f"No previous trading day found for {date_str}")
                return []

            df_prev = self.client.fetch_eod_data(prev_date)
            if df_prev is None or df_prev.empty:
                logger.warning(f"No previous day data for {prev_date}")
                return []
        except Exception as e:
            logger.error(f"Error fetching previous day data: {e}")
            return []

        # Prepare and filter daily data
        df_filtered = prepare_daily_data(df_today, df_prev, self.config)
        if df_filtered is None or df_filtered.empty:
            logger.info(f"No stocks meet minimum turnover criteria for {date_str}")
            return []

        # Process each stock for afterhours activity
        results = []
        for _, row in df_filtered.iterrows():
            symbol = row['code']
            day_close = row['close']

            try:
                result = self._analyze_symbol(symbol, date_str, row, day_close)
                if result:
                    results.append(result)
                    logger.info(
                        f"{symbol}: 4PM ${day_close:.2f} -> AH High ${result['AH_Max_High']:.2f} "
                        f"(+{result['AH_Gain_Pct']:.2f}%) -> 7:59PM ${result['Close_759PM']:.2f} -> "
                        f"Next day ${result['Next_Day_High']:.2f} @ {result['Next_High_Time']} "
                        f"({result['Next_High_vs_759PM_Pct']:+.2f}%)"
                    )

                # Rate limiting
                time.sleep(self.config.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue

        logger.info(f"Found {len(results)} stocks meeting criteria for {date_str}")
        return results

    def _analyze_symbol(
        self,
        symbol: str,
        date_str: str,
        row: pd.Series,
        day_close: float
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single symbol for afterhours activity.

        Args:
            symbol: Stock symbol
            date_str: Analysis date
            row: DataFrame row with daily data
            day_close: 4:00pm closing price

        Returns:
            Analysis result dict if criteria met, None otherwise
        """
        # Fetch intraday data for analysis date
        df_intraday = self.client.fetch_intraday_data(symbol, date_str, interval='1m')
        if df_intraday is None or df_intraday.empty:
            return None

        # Check afterhours conditions
        ah_result = check_afterhours_conditions(df_intraday, day_close, self.config)
        if ah_result is None:
            return None

        # Get next trading day
        try:
            next_date = self.client.get_next_trading_day(date_str)
            if not next_date:
                logger.debug(f"No next trading day found for {symbol}")
                return None
        except Exception as e:
            logger.warning(f"Error getting next trading day for {symbol}: {e}")
            return None

        # Fetch next day intraday data
        df_next = self.client.fetch_intraday_data(symbol, next_date, interval='1m')
        if df_next is None or df_next.empty:
            return None

        # Get next day high
        next_day_result = get_next_day_high(df_next, ah_result['close_759pm'])
        if next_day_result is None:
            return None

        # Compile full result
        return {
            'Date': date_str,
            'Symbol': symbol,
            'Prev_Close': row['prev_close'],
            'Day_Close_4PM': day_close,
            'Daily_Gain_Pct': row['daily_change_pct'],
            'Day_High': row['high'],
            'Turnover_MUSD': row['Turnover (MUSD)'],
            'AH_Max_High': ah_result['max_high'],
            'AH_Max_High_Time': ah_result['max_high_time'],
            'AH_Gain_Pct': ah_result['gain_pct'],
            'AH_Turnover_MUSD': ah_result['turnover_musd'],
            'Close_759PM': ah_result['close_759pm'],
            'Close_759PM_Time': ah_result['close_759pm_time'],
            'Next_Date': next_date,
            'Next_Day_High': next_day_result['next_day_high'],
            'Next_High_Time': next_day_result['next_high_time'],
            'Next_High_vs_759PM_Pct': next_day_result['next_high_vs_759pm_pct']
        }

    def analyze_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Analyze afterhours trading for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with all results
        """
        logger.info(f"Analyzing date range: {start_date} to {end_date}")

        all_results = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            results = self.analyze_date(date_str)
            all_results.extend(results)
            current = current + pd.Timedelta(days=1)

        if not all_results:
            logger.warning("No results found for date range")
            return pd.DataFrame()

        df_results = pd.DataFrame(all_results)
        df_results = df_results.sort_values(
            ['Date', 'Next_High_vs_759PM_Pct'],
            ascending=[True, False]
        )

        logger.info(f"Analysis complete: {len(df_results)} total records")
        return df_results
