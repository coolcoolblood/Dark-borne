# -*- coding: utf-8 -*-
"""Stock Afterhours Analysis Package.

A comprehensive tool for analyzing afterhours stock trading activity using
EODHD API data. Identifies stocks with significant afterhours gains and volume,
and tracks their next-day performance.
"""

__version__ = '10.0.0'
__author__ = 'Stock Analysis Team'

from .config import AnalysisConfig
from .api_client import EODHDClient
from .analysis import AfterhourAnalyzer
from .export import export_to_excel, print_summary_statistics

__all__ = [
    'AnalysisConfig',
    'EODHDClient',
    'AfterhourAnalyzer',
    'export_to_excel',
    'print_summary_statistics',
]
