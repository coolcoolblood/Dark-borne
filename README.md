# Stock Afterhours Analysis

A comprehensive Python tool for analyzing afterhours stock trading activity using EODHD API data. Identifies stocks with significant afterhours gains and volume, and tracks their next-day performance.

## Features

- 🔍 **Automated Stock Screening**: Filters stocks by daily and afterhours trading volume
- 📈 **Afterhours Analysis**: Identifies stocks with significant gains (10%+) during afterhours trading (4:01pm-7:59pm EST)
- 📊 **Next-Day Tracking**: Monitors next-day performance from pre-market through afterhours
- 📁 **Excel Export**: Generates professionally formatted Excel reports with detailed metrics
- ⚙️ **Configurable**: Fully customizable thresholds via environment variables or CLI arguments
- 🔒 **Secure**: API keys stored securely in environment variables, never in source code

## Version 10.0 Improvements

✅ **Critical Fixes Implemented:**
- Removed hardcoded API key (now uses environment variables)
- Cross-platform compatibility (works on Linux, macOS, Windows)
- Removed 50 lines of unused code

✅ **Code Quality Improvements:**
- Refactored into modular Python package structure
- Added comprehensive error handling and logging
- Improved performance with better API client architecture
- Added type hints throughout codebase
- Centralized configuration management

## Requirements

- Python 3.9 or higher
- EODHD API key (get one at [eodhd.com](https://eodhd.com/))

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/coolcoolblood/Dark-borne.git
cd Dark-borne
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your EODHD API key
nano .env
```

Required in `.env`:
```bash
EODHD_API_KEY=your_api_key_here
```

Optional configurations:
```bash
OUTPUT_DIR=/path/to/output/directory  # Default: ~/stock_analysis
MIN_DAY_TURNOVER=5.0                  # Minimum day turnover in M USD
MIN_AH_TURNOVER=1.0                   # Minimum afterhours turnover in M USD
MIN_AH_GAIN=10.0                      # Minimum afterhours gain percentage
```

### 4. (Optional) Load environment variables

If you're using a `.env` file, you can load it automatically:

```bash
# Install python-dotenv if not already installed
pip install python-dotenv

# Load variables before running
export $(cat .env | xargs)
```

Or use `python-dotenv` in your Python code:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Usage

### Basic Usage

Analyze a single date (default: 2025-11-06):
```bash
python -m stock_afterhours.cli
```

Analyze a specific date:
```bash
python -m stock_afterhours.cli 2025-11-06
```

### Advanced Usage

Analyze a date range:
```bash
python -m stock_afterhours.cli --start-date 2025-11-01 --end-date 2025-11-06
```

Custom output directory:
```bash
python -m stock_afterhours.cli 2025-11-06 --output-dir /path/to/output
```

Custom thresholds:
```bash
python -m stock_afterhours.cli 2025-11-06 --min-turnover 10 --min-ah-gain 15
```

Enable verbose logging:
```bash
python -m stock_afterhours.cli 2025-11-06 --verbose
```

### Using as a Python Module

```python
from stock_afterhours import AnalysisConfig, AfterhourAnalyzer
from stock_afterhours.export import export_to_excel, print_summary_statistics

# Load configuration from environment
config = AnalysisConfig.from_env()

# Or create custom configuration
config = AnalysisConfig(
    api_key="your_api_key",
    min_day_turnover_musd=5.0,
    min_ah_turnover_musd=1.0,
    min_ah_gain_pct=10.0
)

# Run analysis
analyzer = AfterhourAnalyzer(config)
df_results = analyzer.analyze_date("2025-11-06")

# Export results
output_path = config.get_output_path("2025-11-06")
export_to_excel(df_results, output_path)
print_summary_statistics(df_results)
```

## Output

The tool generates an Excel file with the following columns:

| Column | Description |
|--------|-------------|
| Date | Analysis date |
| Symbol | Stock ticker symbol |
| Prev Close | Previous day's closing price |
| 4PM Close | Regular market closing price |
| Daily Gain % | Daily gain percentage |
| Day High | Highest price during regular hours |
| Day Turnover M$ | Total daily trading volume in millions USD |
| AH Max High | Highest price during afterhours (4:01pm-7:59pm) |
| AH Max Time (ET) | Time of afterhours high |
| AH Gain % (vs 4PM) | Afterhours gain vs 4PM close |
| AH Turnover M$ | Afterhours trading volume in millions USD |
| 7:59PM Close | Closing price at 7:59pm |
| Next Date | Next trading day |
| Next High | Next day's highest price (4:01am-7:59pm) |
| Next High Time (ET) | Time of next day high |
| Next High vs 7:59PM % | Percentage change from 7:59pm to next day high |

## Analysis Workflow

1. **Fetch EOD Data**: Retrieves end-of-day data for all stocks in the exchange
2. **Filter by Daily Turnover**: Filters stocks with > $5M USD daily turnover (configurable)
3. **Check Afterhours Activity**: For each filtered stock:
   - Fetches intraday data (1-minute intervals)
   - Checks for >= $1M USD turnover during afterhours (4:01pm-7:59pm EST)
   - Checks for >= 10% gain vs 4:00pm close
4. **Track Next Day Performance**: Records next day's high price (4:01am-7:59pm EST)
5. **Export Results**: Generates formatted Excel report with all metrics

## Project Structure

```
Dark-borne/
├── stock_afterhours/          # Main package
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── api_client.py         # EODHD API client
│   ├── data_processing.py    # Data filtering and calculations
│   ├── analysis.py           # Core analysis logic
│   ├── export.py             # Excel export functionality
│   └── cli.py                # Command-line interface
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment configuration
├── CODE_REVIEW.md           # Comprehensive code review
└── README.md                # This file
```

## Configuration

All configuration can be set via:
1. **Environment variables** (recommended for API keys)
2. **Command-line arguments** (for one-off customizations)
3. **Code** (when using as a Python module)

### Configuration Options

| Option | Env Variable | CLI Argument | Default | Description |
|--------|-------------|--------------|---------|-------------|
| API Key | `EODHD_API_KEY` | - | Required | EODHD API key |
| Output Dir | `OUTPUT_DIR` | `--output-dir` | `~/stock_analysis` | Output directory |
| Exchange | `EXCHANGE_CODE` | - | `US` | Exchange code |
| Min Day Turnover | `MIN_DAY_TURNOVER` | `--min-turnover` | `5.0` | Min daily turnover (M USD) |
| Min AH Turnover | `MIN_AH_TURNOVER` | - | `1.0` | Min afterhours turnover (M USD) |
| Min AH Gain | `MIN_AH_GAIN` | `--min-ah-gain` | `10.0` | Min afterhours gain (%) |

## Troubleshooting

### API Key Issues

```
ValueError: EODHD_API_KEY environment variable is required
```

**Solution**: Make sure your `.env` file exists and contains your API key, or export it directly:
```bash
export EODHD_API_KEY="your_api_key_here"
```

### Permission Issues

```
PermissionError: [Errno 13] Permission denied
```

**Solution**: Ensure the output directory is writable:
```bash
chmod -R 755 ~/stock_analysis
```

Or specify a different output directory:
```bash
python -m stock_afterhours.cli 2025-11-06 --output-dir /tmp/stock_analysis
```

### No Data Found

```
No matching records found
```

**Solution**: This means no stocks met the criteria on that date. Try:
- Lowering the thresholds: `--min-turnover 3 --min-ah-gain 5`
- Checking if it was a trading day
- Verifying your API key has access to the data

## Performance Tips

- **Rate Limiting**: The tool includes built-in rate limiting (0.5s between API calls) to avoid hitting API limits
- **Parallel Requests**: Future versions will implement concurrent API requests for better performance
- **Caching**: Consider caching EOD data locally if analyzing multiple date ranges

## Contributing

Contributions are welcome! Please see [CODE_REVIEW.md](CODE_REVIEW.md) for improvement suggestions and development guidelines.

## Known Limitations

- Sequential API calls (concurrent requests planned for v11.0)
- EODHD API rate limits apply
- Historical intraday data may have gaps
- Afterhours data availability varies by stock

## License

This project is open source. Please review the license file for terms and conditions.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Review the [CODE_REVIEW.md](CODE_REVIEW.md) for detailed technical information

## Changelog

### Version 10.0 (2025-11-12)
- ✅ **CRITICAL**: Removed hardcoded API key, now uses environment variables
- ✅ **CRITICAL**: Fixed cross-platform path compatibility
- ✅ Refactored into modular Python package structure
- ✅ Added comprehensive error handling and logging
- ✅ Added type hints throughout codebase
- ✅ Centralized configuration management
- ✅ Improved CLI with argparse
- ✅ Added detailed documentation

### Version 9.1 (Previous)
- Optimized filter logic for better performance
- Improved timezone handling
- Bug fixes and stability improvements

---

**Made with ❤️ for stock market analysis**
