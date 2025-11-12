# -*- coding: utf-8 -*-
"""EODHD API client for fetching stock market data."""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import requests
import pandas as pd

from .config import AnalysisConfig

logger = logging.getLogger(__name__)


class EODHDClient:
    """Client for interacting with EODHD API.

    Attributes:
        config: Analysis configuration
        session: Requests session for connection reuse
    """

    def __init__(self, config: AnalysisConfig):
        """Initialize EODHD API client.

        Args:
            config: Analysis configuration with API key and settings
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> requests.Response:
        """Make HTTP request with retry logic.

        Args:
            url: API endpoint URL
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        if timeout is None:
            timeout = self.config.api_timeout

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.config.max_retries}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}/{self.config.max_retries}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise

            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise
                logger.warning(f"Request failed: {e}")
                time.sleep(1)

        raise requests.exceptions.RequestException("Request failed after retries")

    def is_trading_day(self, date_str: str) -> bool:
        """Check if a date is a trading day.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            True if trading day, False otherwise
        """
        try:
            url = f"https://eodhd.com/api/eod-bulk-last-day/{self.config.exchange_code}"
            params = {
                'date': date_str,
                'api_token': self.config.api_key,
                'fmt': 'json'
            }

            response = self._make_request(url, params)
            if response.status_code == 200:
                data = response.json()
                # Valid trading day should have substantial data
                is_valid = len(data) > 500
                logger.info(f"{date_str}: {'Trading day' if is_valid else 'Non-trading day'}")
                return is_valid

            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check trading day {date_str}: {e}")
            raise

    def fetch_eod_data(self, date_str: str) -> Optional[pd.DataFrame]:
        """Fetch end-of-day data for all stocks on a specific date.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            DataFrame with EOD data, or None if no data available
        """
        try:
            url = f"https://eodhd.com/api/eod-bulk-last-day/{self.config.exchange_code}"
            params = {
                'date': date_str,
                'api_token': self.config.api_key,
                'fmt': 'json'
            }

            response = self._make_request(url, params)

            if response.status_code == 200:
                data = response.json()
                if not data:
                    logger.warning(f"No EOD data for {date_str}")
                    return None

                df = pd.DataFrame(data)
                logger.info(f"Fetched {len(df)} stocks for {date_str}")
                return df

            logger.warning(f"Failed to fetch EOD data for {date_str}: status {response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch EOD data for {date_str}: {e}")
            raise

    def fetch_intraday_data(
        self,
        symbol: str,
        date_str: Optional[str] = None,
        interval: str = '1m'
    ) -> Optional[pd.DataFrame]:
        """Fetch intraday data for a specific symbol.

        Args:
            symbol: Stock symbol
            date_str: Date string in YYYY-MM-DD format (optional, for filtering)
            interval: Data interval (1m, 5m, etc.)

        Returns:
            DataFrame with intraday data, or None if not available
        """
        try:
            symbol_with_exchange = f"{symbol}.{self.config.exchange_code}"
            url = f"https://eodhd.com/api/intraday/{symbol_with_exchange}"

            params = {
                'api_token': self.config.api_key,
                'interval': interval,
                'fmt': 'json'
            }

            response = self._make_request(url, params)

            if response.status_code == 200:
                data = response.json()

                if not isinstance(data, list) or len(data) == 0:
                    logger.debug(f"No intraday data for {symbol}")
                    return None

                df = pd.DataFrame(data)

                if 'datetime' not in df.columns:
                    logger.warning(f"Invalid intraday data format for {symbol}")
                    return None

                # Convert datetime and timezone (UTC -> US/Eastern)
                df['datetime'] = pd.to_datetime(df['datetime'])
                if df['datetime'].dt.tz is None:
                    df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
                else:
                    df['datetime'] = df['datetime'].dt.tz_convert('US/Eastern')

                # Filter by date if specified
                if date_str:
                    df['date_only'] = df['datetime'].dt.date
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    df = df[df['date_only'] == target_date]

                logger.debug(f"Fetched {len(df)} intraday records for {symbol}")
                return df

            logger.debug(f"Failed to fetch intraday data for {symbol}: status {response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch intraday data for {symbol}: {e}")
            return None

    def get_previous_trading_day(self, date_str: str) -> Optional[str]:
        """Get the previous trading day before a given date.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Previous trading day as YYYY-MM-DD string, or None if not found
        """
        current = datetime.strptime(date_str, '%Y-%m-%d')

        for days_back in range(1, 10):  # Extended to 10 days to handle long weekends/holidays
            prev_date = current - timedelta(days=days_back)

            # Skip weekends
            if prev_date.weekday() >= 5:
                continue

            prev_date_str = prev_date.strftime('%Y-%m-%d')
            try:
                if self.is_trading_day(prev_date_str):
                    return prev_date_str
            except Exception as e:
                logger.warning(f"Error checking trading day {prev_date_str}: {e}")
                continue

        logger.error(f"Could not find previous trading day for {date_str}")
        return None

    def get_next_trading_day(self, date_str: str) -> Optional[str]:
        """Get the next trading day after a given date.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Next trading day as YYYY-MM-DD string, or None if not found
        """
        current = datetime.strptime(date_str, '%Y-%m-%d')

        for days_ahead in range(1, 10):  # Extended to 10 days
            next_date = current + timedelta(days=days_ahead)

            # Skip weekends
            if next_date.weekday() >= 5:
                continue

            next_date_str = next_date.strftime('%Y-%m-%d')
            try:
                if self.is_trading_day(next_date_str):
                    return next_date_str
            except Exception as e:
                logger.warning(f"Error checking trading day {next_date_str}: {e}")
                continue

        logger.error(f"Could not find next trading day for {date_str}")
        return None
