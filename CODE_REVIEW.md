# Stock Afterhours Analysis - Code Review

## Executive Summary

This script analyzes afterhours stock trading data using the EODHD API. While functionally sound, there are **critical security issues**, **cross-platform compatibility problems**, and several areas for improvement in code quality, performance, and maintainability.

---

## 🔴 CRITICAL ISSUES

### 1. **Security: Exposed API Key**
**Severity: CRITICAL**

```python
api_key = "68c4137d59cf88.99973900"  # ❌ NEVER commit API keys to source control
```

**Risk:**
- API key is exposed in plain text
- If committed to git, it's in version history forever
- Can lead to unauthorized API usage and potential charges

**Fix:**
```python
import os
api_key = os.getenv('EODHD_API_KEY')
if not api_key:
    raise ValueError("EODHD_API_KEY environment variable not set")
```

---

### 2. **Cross-Platform Compatibility: Windows-Only Paths**
**Severity: HIGH**

```python
log_path = r"C:\Users\iMac windows10\OneDrive\股票\美股\failed_symbols.txt"
output_path = rf"C:\Users\iMac windows10\OneDrive\股票\美股\afterhours_analysis_{analysis_date}.xlsx"
```

**Issues:**
- Hardcoded Windows paths won't work on Linux/Mac
- `log_path` is defined but never used
- No user configurability

**Fix:**
```python
from pathlib import Path

# Use user's home directory + configurable output directory
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', Path.home() / 'stock_analysis'))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
output_path = OUTPUT_DIR / f"afterhours_analysis_{analysis_date}.xlsx"
```

---

## 🟡 HIGH PRIORITY IMPROVEMENTS

### 3. **Dead Code: Unused Functions**

Two functions are defined but never called:
- `get_nasdaq_earnings()` - 29 lines
- `get_earnings_stocks_nasdaq()` - 21 lines

**Impact:** Code bloat, confusion for maintainers

**Recommendation:**
- Remove if not needed, or
- Document why they're kept for future use
- Consider moving to a separate module

---

### 4. **Error Handling: Silent Failures**

**Issue 1:** Trading day check failures return `False`
```python
def is_trading_day(date_str):
    # ...
    except Exception as e:
        print(f"   Warning: Failed to check trading day {date_str}")
        return False  # ❌ Assumes non-trading day on network error
```

**Issue 2:** Generic exception catching hides specific errors
```python
except Exception as e:  # ❌ Too broad
    print(f"   Warning: Failed to fetch data for {date_str}")
```

**Fix:**
```python
import logging

def is_trading_day(date_str):
    try:
        # ... existing code ...
    except requests.exceptions.RequestException as e:
        logging.error(f"API error checking trading day {date_str}: {e}")
        raise  # Let caller decide how to handle
    except Exception as e:
        logging.exception(f"Unexpected error checking trading day {date_str}")
        raise
```

---

### 5. **Performance: Sequential API Calls**

**Current:** Processes stocks one-by-one with 0.5s delay
```python
for idx, (_, row) in enumerate(df_filtered.iterrows()):
    symbol = row['code']
    ah_result = check_afterhours_conditions(symbol, date_str, day_close)
    # ...
    time.sleep(0.5)  # ❌ Sequential = slow
```

**Impact:**
- For 100 stocks: ~50+ seconds just in sleep delays
- Network latency adds more time
- No parallelization

**Fix:** Use concurrent requests
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_symbol(symbol, date_str, row):
    """Process a single symbol"""
    # ... existing logic ...
    return result

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(process_symbol, row['code'], date_str, row): row['code']
        for _, row in df_filtered.iterrows()
    }

    for future in as_completed(futures):
        symbol = futures[future]
        try:
            result = future.result()
            if result:
                all_results.append(result)
                print(f"      {symbol}: ...")
        except Exception as e:
            logging.error(f"Failed to process {symbol}: {e}")
```

**Benefit:** ~10x faster for large datasets (respecting API rate limits)

---

### 6. **Configuration Management**

**Issues:**
- Magic numbers scattered throughout (`5`, `1`, `10` for thresholds)
- No central configuration
- Hard to adjust parameters without editing code

**Current:**
```python
df_filtered = df[df['Turnover (MUSD)'] > 5].copy()  # ❌ Magic number
# ...
if turnover_musd < 1:  # ❌ Magic number
    return None
# ...
if gain_pct < 10:  # ❌ Magic number
    return None
```

**Fix:**
```python
from dataclasses import dataclass

@dataclass
class AnalysisConfig:
    """Configuration for afterhours analysis"""
    min_day_turnover_musd: float = 5.0
    min_ah_turnover_musd: float = 1.0
    min_ah_gain_pct: float = 10.0
    api_timeout: int = 20
    max_retries: int = 3
    rate_limit_delay: float = 0.5

    @classmethod
    def from_env(cls):
        """Load config from environment variables"""
        return cls(
            min_day_turnover_musd=float(os.getenv('MIN_DAY_TURNOVER', '5.0')),
            min_ah_turnover_musd=float(os.getenv('MIN_AH_TURNOVER', '1.0')),
            min_ah_gain_pct=float(os.getenv('MIN_AH_GAIN', '10.0')),
        )

# Usage:
config = AnalysisConfig.from_env()
df_filtered = df[df['Turnover (MUSD)'] > config.min_day_turnover_musd].copy()
```

---

## 🟢 MEDIUM PRIORITY IMPROVEMENTS

### 7. **Code Organization**

**Issue:** 467-line monolithic script with mixed concerns

**Recommendation:** Split into modules:

```
stock_afterhours/
├── __init__.py
├── config.py          # Configuration management
├── api_client.py      # EODHD API wrapper
├── data_processing.py # Data filtering and calculation
├── analysis.py        # Core analysis logic
├── export.py          # Excel export functionality
└── cli.py             # Command-line interface
```

**Benefits:**
- Easier testing
- Better maintainability
- Reusable components
- Clearer separation of concerns

---

### 8. **Type Hints**

**Current:** No type annotations
```python
def get_previous_trading_day(date_str):  # ❌ No types
    # ...
```

**Improved:**
```python
from typing import Optional
from datetime import datetime

def get_previous_trading_day(date_str: str) -> Optional[str]:
    """
    Get the previous trading day before the given date.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Previous trading day as YYYY-MM-DD string, or None if not found
    """
    # ...
```

**Benefits:**
- Better IDE support
- Catches type errors early
- Self-documenting code
- Enables static type checking with mypy

---

### 9. **Logging Instead of Print Statements**

**Current:**
```python
print(f"   Step 1: {len(df_filtered)} stocks with turnover > 5M USD")
print(f"      Warning: Failed to check afterhours conditions: {e}")
```

**Issues:**
- No log levels
- No log file output
- Can't disable debug messages easily
- No timestamps

**Fix:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'analysis_{date_str}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage:
logger.info(f"Step 1: {len(df_filtered)} stocks with turnover > 5M USD")
logger.warning(f"Failed to check afterhours conditions for {symbol}: {e}")
logger.debug(f"API response: {data}")
```

---

### 10. **Data Validation**

**Issue:** Minimal validation of API responses

**Current:**
```python
if response.status_code == 200:
    data = response.json()
    if not data:
        return None
    df = pd.DataFrame(data)  # ❌ What if data is malformed?
```

**Improved:**
```python
def validate_eod_response(data: list) -> bool:
    """Validate EOD API response structure"""
    if not isinstance(data, list):
        return False
    if not data:
        return False

    required_fields = {'code', 'open', 'high', 'low', 'close', 'volume'}
    sample = data[0]

    return all(field in sample for field in required_fields)

# Usage:
data = response.json()
if not validate_eod_response(data):
    logger.error("Invalid API response format")
    return None
```

---

### 11. **Timezone Handling Edge Cases**

**Current implementation is good but could be more defensive:**

```python
# Current:
df['datetime'] = pd.to_datetime(df['datetime'])
if df['datetime'].dt.tz is None:
    df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
else:
    df['datetime'] = df['datetime'].dt.tz_convert('US/Eastern')
```

**Potential issue:** What if API returns inconsistent timezone formats?

**Improved:**
```python
from zoneinfo import ZoneInfo  # Python 3.9+

def normalize_to_eastern(dt_series: pd.Series) -> pd.Series:
    """Convert datetime series to US/Eastern timezone"""
    dt_series = pd.to_datetime(dt_series, errors='coerce')

    # Handle timezone-naive datetimes
    if dt_series.dt.tz is None:
        # Assume UTC for naive datetimes from API
        dt_series = dt_series.dt.tz_localize('UTC')

    # Convert to Eastern
    return dt_series.dt.tz_convert('US/Eastern')

# Usage:
df['datetime'] = normalize_to_eastern(df['datetime'])
```

---

### 12. **Memory Efficiency**

**Issue:** Loads full dataframes into memory for each date

**For large date ranges, consider:**
```python
# Use chunking for large datasets
def process_date_range_chunked(start_date, end_date, chunk_size=10):
    """Process date range in chunks to manage memory"""
    dates = pd.date_range(start_date, end_date, freq='D')

    for i in range(0, len(dates), chunk_size):
        chunk = dates[i:i + chunk_size]
        results = process_dates(chunk)
        yield results

# Write results incrementally to Excel instead of accumulating all in memory
```

---

## 🔵 NICE-TO-HAVE IMPROVEMENTS

### 13. **Testing**

**Missing:** No unit tests, integration tests, or test data

**Recommended test structure:**
```
tests/
├── __init__.py
├── test_api_client.py
├── test_data_processing.py
├── test_analysis.py
├── fixtures/
│   ├── sample_eod_data.json
│   └── sample_intraday_data.json
└── conftest.py
```

**Example test:**
```python
import pytest
from unittest.mock import Mock, patch
from your_module import check_afterhours_conditions

def test_afterhours_conditions_met():
    """Test that stock meeting conditions is detected"""
    with patch('requests.Session.get') as mock_get:
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'datetime': '2024-01-01 16:30:00',
                'close': 110,
                'high': 112,
                'volume': 1000000
            }
        ]
        mock_get.return_value = mock_response

        result = check_afterhours_conditions('TEST', '2024-01-01', 100)

        assert result is not None
        assert result['gain_pct'] >= 10
```

---

### 14. **Progress Bar**

**Current:** Simple print statements
**Enhancement:** Use `tqdm` for better progress visualization

```python
from tqdm import tqdm

for _, row in tqdm(df_filtered.iterrows(), total=len(df_filtered), desc="Processing stocks"):
    symbol = row['code']
    # ...
```

---

### 15. **Caching**

**Optimization:** Cache trading day checks

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def is_trading_day(date_str: str) -> bool:
    """Check if date is a trading day (cached)"""
    # ... existing logic ...
```

---

### 16. **Command-Line Interface Improvements**

**Current:** Minimal CLI options

**Enhancement with `argparse`:**
```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description='Analyze afterhours stock trading activity'
    )
    parser.add_argument(
        'date',
        nargs='?',
        default='2025-11-06',
        help='Analysis date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='Output directory for Excel files'
    )
    parser.add_argument(
        '--min-turnover',
        type=float,
        default=5.0,
        help='Minimum day turnover in M USD'
    )
    parser.add_argument(
        '--min-ah-gain',
        type=float,
        default=10.0,
        help='Minimum afterhours gain percentage'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--date-range',
        nargs=2,
        metavar=('START', 'END'),
        help='Analyze a date range (START END in YYYY-MM-DD)'
    )

    return parser.parse_args()
```

---

### 17. **Data Quality Checks**

**Add sanity checks for data anomalies:**

```python
def validate_stock_data(row: pd.Series) -> bool:
    """Validate stock data for anomalies"""
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
        logger.warning(f"Data quality issue for {row['code']}: {row.to_dict()}")
        return False

    return True
```

---

### 18. **Documentation**

**Missing:**
- README.md with setup instructions
- requirements.txt for dependencies
- Example usage
- API documentation

**Create:**
```markdown
# Stock Afterhours Analysis

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export EODHD_API_KEY="your_api_key_here"
   export OUTPUT_DIR="/path/to/output"
   ```

3. Run analysis:
   ```bash
   python afterhours_analysis.py 2025-11-06
   ```

## Configuration

See `config.py` for available options.

## Output

Creates Excel file with columns:
- Date: Analysis date
- Symbol: Stock ticker
- ...
```

---

## 📊 Summary of Issues

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 1 | 0 | 0 | 0 |
| Compatibility | 0 | 1 | 0 | 0 |
| Code Quality | 0 | 1 | 5 | 3 |
| Performance | 0 | 1 | 1 | 1 |
| Testing | 0 | 0 | 1 | 0 |
| **Total** | **1** | **3** | **7** | **4** |

---

## 🎯 Recommended Action Plan

### Phase 1: Critical Fixes (Do Now)
1. ✅ Remove hardcoded API key, use environment variable
2. ✅ Fix cross-platform path compatibility
3. ✅ Remove or document unused code

### Phase 2: High Priority (This Week)
4. ✅ Improve error handling and logging
5. ✅ Add configuration management
6. ✅ Optimize performance with concurrent requests

### Phase 3: Medium Priority (This Month)
7. ✅ Refactor into modules
8. ✅ Add type hints
9. ✅ Implement proper logging
10. ✅ Add data validation
11. ✅ Improve CLI

### Phase 4: Nice-to-Have (When Time Permits)
12. ✅ Add unit tests
13. ✅ Add progress bars
14. ✅ Add caching
15. ✅ Write documentation

---

## 💡 Quick Wins (Low Effort, High Impact)

1. **Environment variables for secrets** (15 min)
2. **Use pathlib for paths** (15 min)
3. **Remove unused functions** (5 min)
4. **Add type hints to main functions** (30 min)
5. **Create requirements.txt** (5 min)

---

## 🔗 Useful Resources

- [EODHD API Documentation](https://eodhd.com/financial-apis/)
- [Python Best Practices](https://docs.python-guide.org/)
- [pandas Performance Tips](https://pandas.pydata.org/docs/user_guide/enhancingperf.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

**Reviewed:** 2025-11-12
**Reviewer:** Claude Code Analysis
**Version:** 9.1
