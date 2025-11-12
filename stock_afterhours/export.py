# -*- coding: utf-8 -*-
"""Excel export functionality for analysis results."""

import logging
from pathlib import Path

import pandas as pd
import xlsxwriter

logger = logging.getLogger(__name__)


def export_to_excel(df: pd.DataFrame, output_path: Path) -> None:
    """Export analysis results to formatted Excel file.

    Args:
        df: DataFrame with analysis results
        output_path: Path to output Excel file

    Raises:
        Exception: If export fails
    """
    if df.empty:
        logger.warning("No data to export")
        return

    logger.info(f"Exporting {len(df)} records to Excel: {output_path}")

    try:
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Results')
            workbook = writer.book
            worksheet = writer.sheets['Results']

            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1,
                'font_size': 11
            })

            date_format = workbook.add_format({
                'num_format': 'yyyy-mm-dd',
                'border': 1,
                'align': 'center'
            })

            price_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1,
                'align': 'right'
            })

            percent_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1,
                'align': 'center'
            })

            number_format = workbook.add_format({
                'num_format': '#,##0.00',
                'border': 1,
                'align': 'right'
            })

            time_format = workbook.add_format({
                'border': 1,
                'align': 'center'
            })

            # Column headers with friendly names
            headers = {
                'Date': 'Date',
                'Symbol': 'Symbol',
                'Prev_Close': 'Prev Close',
                'Day_Close_4PM': '4PM Close',
                'Daily_Gain_Pct': 'Daily Gain %',
                'Day_High': 'Day High',
                'Turnover_MUSD': 'Day Turnover M$',
                'AH_Max_High': 'AH Max High',
                'AH_Max_High_Time': 'AH Max Time (ET)',
                'AH_Gain_Pct': 'AH Gain % (vs 4PM)',
                'AH_Turnover_MUSD': 'AH Turnover M$',
                'Close_759PM': '7:59PM Close',
                'Close_759PM_Time': '7:59PM Time (ET)',
                'Next_Date': 'Next Date',
                'Next_Day_High': 'Next High',
                'Next_High_Time': 'Next High Time (ET)',
                'Next_High_vs_759PM_Pct': 'Next High vs 7:59PM %'
            }

            # Write headers
            for col_num, col_name in enumerate(df.columns):
                english_name = headers.get(col_name, col_name)
                worksheet.write(0, col_num, english_name, header_format)

            # Set column widths
            column_widths = [12, 12, 12, 12, 12, 12, 12, 16, 14, 14, 16, 12, 14, 12, 12, 16, 18]
            for i, width in enumerate(column_widths):
                if i < len(df.columns):
                    worksheet.set_column(i, i, width)

            # Write data with formatting
            for row_num in range(1, len(df) + 1):
                row_data = df.iloc[row_num - 1]

                for col_num, col_name in enumerate(df.columns):
                    value = row_data[col_name]

                    if col_name in ['Date', 'Next_Date']:
                        worksheet.write(row_num, col_num, value, date_format)
                    elif col_name in ['Prev_Close', 'Day_Close_4PM', 'Day_High',
                                     'AH_Max_High', 'Close_759PM', 'Next_Day_High']:
                        worksheet.write(row_num, col_num, value, price_format)
                    elif col_name in ['Daily_Gain_Pct', 'AH_Gain_Pct', 'Next_High_vs_759PM_Pct']:
                        worksheet.write(row_num, col_num, value / 100, percent_format)
                    elif col_name in ['AH_Max_High_Time', 'Close_759PM_Time', 'Next_High_Time']:
                        worksheet.write(row_num, col_num, value, time_format)
                    elif col_name in ['Turnover_MUSD', 'AH_Turnover_MUSD']:
                        worksheet.write(row_num, col_num, value, number_format)
                    else:
                        worksheet.write(row_num, col_num, value, number_format)

        logger.info(f"Excel file saved successfully: {output_path}")

    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise


def print_summary_statistics(df: pd.DataFrame) -> None:
    """Print summary statistics for analysis results.

    Args:
        df: DataFrame with analysis results
    """
    if df.empty:
        logger.info("No records to summarize")
        return

    print("\n" + "=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    print(f"Total Records: {len(df)}")
    print(f"Unique Dates: {df['Date'].nunique()}")
    print(f"Unique Symbols: {df['Symbol'].nunique()}")

    print(f"\nAfterHours Performance (4:01pm-7:59pm EST vs 4PM Close):")
    print(f"   Average AH Gain: {df['AH_Gain_Pct'].mean():+.2f}%")
    print(f"   Median AH Gain: {df['AH_Gain_Pct'].median():+.2f}%")
    print(f"   Max AH Gain: {df['AH_Gain_Pct'].max():+.2f}%")
    print(f"   Min AH Gain: {df['AH_Gain_Pct'].min():+.2f}%")
    print(f"   Average AH Turnover: ${df['AH_Turnover_MUSD'].mean():.2f}M")

    print(f"\nNext Day High vs 7:59PM Close Comparison:")
    print(f"   Average Gain: {df['Next_High_vs_759PM_Pct'].mean():+.2f}%")
    print(f"   Median Gain: {df['Next_High_vs_759PM_Pct'].median():+.2f}%")
    print(f"   Max Gain: {df['Next_High_vs_759PM_Pct'].max():+.2f}%")
    print(f"   Min Gain: {df['Next_High_vs_759PM_Pct'].min():+.2f}%")
    print(f"   Up Records: {len(df[df['Next_High_vs_759PM_Pct'] > 0])} "
          f"({len(df[df['Next_High_vs_759PM_Pct'] > 0]) / len(df) * 100:.1f}%)")
    print(f"   Down Records: {len(df[df['Next_High_vs_759PM_Pct'] < 0])} "
          f"({len(df[df['Next_High_vs_759PM_Pct'] < 0]) / len(df) * 100:.1f}%)")

    print(f"\nTop 5 Performers (Next Day High vs 7:59PM Close):")
    print("-" * 110)
    print(f"{'Date':<12} {'Symbol':<8} {'4PM Close':<12} {'AH Gain%':<12} "
          f"{'7:59PM':<12} {'Next High':<12} {'Gain%':<12}")
    print("-" * 110)

    top_5 = df.nlargest(5, 'Next_High_vs_759PM_Pct')
    for _, row in top_5.iterrows():
        print(f"{row['Date']:<12} {row['Symbol']:<8} ${row['Day_Close_4PM']:>10.2f} "
              f"{row['AH_Gain_Pct']:>10.2f}% ${row['Close_759PM']:>10.2f} "
              f"${row['Next_Day_High']:>10.2f} {row['Next_High_vs_759PM_Pct']:>10.2f}%")

    print(f"\nBottom 5 Performers (Next Day High vs 7:59PM Close):")
    print("-" * 110)
    print(f"{'Date':<12} {'Symbol':<8} {'4PM Close':<12} {'AH Gain%':<12} "
          f"{'7:59PM':<12} {'Next High':<12} {'Gain%':<12}")
    print("-" * 110)

    bottom_5 = df.nsmallest(5, 'Next_High_vs_759PM_Pct')
    for _, row in bottom_5.iterrows():
        print(f"{row['Date']:<12} {row['Symbol']:<8} ${row['Day_Close_4PM']:>10.2f} "
              f"{row['AH_Gain_Pct']:>10.2f}% ${row['Close_759PM']:>10.2f} "
              f"${row['Next_Day_High']:>10.2f} {row['Next_High_vs_759PM_Pct']:>10.2f}%")

    print("=" * 80)
