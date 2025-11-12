# -*- coding: utf-8 -*-
"""Data processing and filtering for stock afterhours analysis."""

import logging
from typing import Optional, Dict, Any

import pandas as pd

from .config import AnalysisConfig

logger = logging.getLogger(__name__)


def prepare_daily_data(
    df_today: pd.DataFrame,
    df_prev: pd.DataFrame,
    config: AnalysisConfig
) -> Optional[pd.DataFrame]:
    """Prepare and merge daily trading data with previous day data.

    Args:
        df_today: Today's EOD data
        df_prev: Previous day's EOD data
        config: Analysis configuration

    Returns:
        Merged and filtered DataFrame, or None if no valid data
    """
    try:
        # Select and rename columns
        df_today = df_today[['code', 'open', 'high', 'low', 'close', 'volume']].copy()
        df_prev = df_prev[['code', 'close']].rename(columns={'close': 'prev_close'})

        # Convert to numeric
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df_today[col] = pd.to_numeric(df_today[col], errors='coerce')
        df_prev['prev_close'] = pd.to_numeric(df_prev['prev_close'], errors='coerce')

        # Merge datasets
        df = pd.merge(df_today, df_prev, on='code', how='inner')

        # Drop invalid data
        df = df.dropna(subset=numeric_cols + ['prev_close'])
        df = df[(df['volume'] > 0) & (df['prev_close'] > 0) & (df['close'] > 0)]

        # Calculate daily metrics
        df['daily_change_pct'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
        df['Turnover (MUSD)'] = df['close'] * df['volume'] / 1_000_000

        # Filter by minimum daily turnover
        df_filtered = df[df['Turnover (MUSD)'] > config.min_day_turnover_musd].copy()

        logger.info(f"Filtered to {len(df_filtered)} stocks with turnover > ${config.min_day_turnover_musd}M USD")

        return df_filtered if not df_filtered.empty else None

    except Exception as e:
        logger.error(f"Error preparing daily data: {e}")
        return None


def validate_stock_data(row: pd.Series) -> bool:
    """Validate stock data for anomalies.

    Args:
        row: DataFrame row with stock data

    Returns:
        True if data is valid, False otherwise
    """
    checks = [
        row['high'] >= row['close'],
        row['high'] >= row['open'],
        row['high'] >= row['low'],
        row['low'] <= row['close'],
        row['low'] <= row['open'],
        row['volume'] >= 0,
        row['close'] > 0,
    ]

    if not all(checks):
        logger.warning(f"Data quality issue for {row['code']}: high={row['high']}, "
                      f"low={row['low']}, open={row['open']}, close={row['close']}")
        return False

    return True


def check_afterhours_conditions(
    df_intraday: pd.DataFrame,
    day_close_price: float,
    config: AnalysisConfig
) -> Optional[Dict[str, Any]]:
    """Check if stock meets afterhours conditions.

    Checks for:
    1. Afterhours turnover >= min_ah_turnover_musd (4:01pm-7:59pm EST)
    2. Afterhours gain >= min_ah_gain_pct (vs 4pm close)

    Args:
        df_intraday: Intraday data with datetime in US/Eastern timezone
        day_close_price: The 4:00pm closing price (regular market close)
        config: Analysis configuration

    Returns:
        Dict with afterhours data if conditions met, None otherwise
    """
    try:
        # Extract hour and minute in ET
        df_intraday['hour_et'] = df_intraday['datetime'].dt.hour
        df_intraday['minute_et'] = df_intraday['datetime'].dt.minute

        # Filter for 4:01pm-7:59pm EST (16:01-19:59) - after hours
        mask = (
            ((df_intraday['hour_et'] == 16) & (df_intraday['minute_et'] >= 1)) |
            (df_intraday['hour_et'].isin(range(17, 20)))
        )

        df_filtered = df_intraday[mask].copy()

        if df_filtered.empty:
            return None

        # Clean data
        df_filtered['close'] = pd.to_numeric(df_filtered['close'], errors='coerce')
        df_filtered['high'] = pd.to_numeric(df_filtered['high'], errors='coerce')
        df_filtered['volume'] = pd.to_numeric(df_filtered['volume'], errors='coerce')
        df_filtered = df_filtered[(df_filtered['close'] > 0) & (df_filtered['high'] > 0)]

        if df_filtered.empty:
            return None

        # Step 1: Check afterhours turnover first (more efficient to filter by this first)
        total_volume = df_filtered['volume'].sum()
        avg_price = df_filtered['close'].mean()
        turnover_musd = (avg_price * total_volume) / 1_000_000

        # Early exit if turnover < threshold
        if turnover_musd < config.min_ah_turnover_musd:
            return None

        # Step 2: Only calculate gain if turnover condition is met
        max_high = float(df_filtered['high'].max())
        max_idx = df_filtered['high'].idxmax()
        max_high_time = df_filtered.loc[max_idx, 'datetime'].strftime('%H:%M:%S')

        # Calculate gain percentage from 4:00pm close (regular market close)
        gain_pct = ((max_high - day_close_price) / day_close_price) * 100

        # Early exit if gain < threshold
        if gain_pct < config.min_ah_gain_pct:
            return None

        # Both conditions met, get remaining data
        close_759pm = float(df_filtered['close'].iloc[-1])
        close_759pm_time = df_filtered['datetime'].iloc[-1].strftime('%H:%M:%S')

        return {
            'base_price_4pm': day_close_price,
            'max_high': max_high,
            'max_high_time': max_high_time,
            'close_759pm': close_759pm,
            'close_759pm_time': close_759pm_time,
            'gain_pct': gain_pct,
            'turnover_musd': turnover_musd
        }

    except Exception as e:
        logger.warning(f"Error checking afterhours conditions: {e}")
        return None


def get_next_day_high(
    df_intraday: pd.DataFrame,
    close_759pm: float
) -> Optional[Dict[str, Any]]:
    """Get next trading day high between 4:01am-7:59pm EST.

    Args:
        df_intraday: Intraday data with datetime in US/Eastern timezone
        close_759pm: Previous day's 7:59pm closing price

    Returns:
        Dict with next day high data, or None if not available
    """
    try:
        # Extract hour and minute in ET
        df_intraday['hour_et'] = df_intraday['datetime'].dt.hour
        df_intraday['minute_et'] = df_intraday['datetime'].dt.minute

        # Filter for 4:01am-7:59pm EST (4:01-19:59)
        mask = (
            ((df_intraday['hour_et'] == 4) & (df_intraday['minute_et'] >= 1)) |
            (df_intraday['hour_et'].isin(range(5, 20)))
        )
        df_filtered = df_intraday[mask].copy()

        if df_filtered.empty:
            return None

        # Get the maximum high price
        df_filtered['high'] = pd.to_numeric(df_filtered['high'], errors='coerce')
        df_filtered = df_filtered[df_filtered['high'] > 0]

        if df_filtered.empty:
            return None

        # Find the row with maximum high and get its time
        max_idx = df_filtered['high'].idxmax()
        max_row = df_filtered.loc[max_idx]
        max_high = float(max_row['high'])
        time_str = max_row['datetime'].strftime('%H:%M:%S')

        # Calculate percentage change from 7:59pm close to next day high
        pct_change = ((max_high - close_759pm) / close_759pm) * 100

        return {
            'next_day_high': max_high,
            'next_high_time': time_str,
            'next_high_vs_759pm_pct': pct_change
        }

    except Exception as e:
        logger.warning(f"Error getting next day high: {e}")
        return None
