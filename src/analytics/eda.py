"""
UAE Retail Intelligence Platform
Reusable Exploratory Data Analysis utilities.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


EDA_STYLE = "whitegrid"

FIGURE_DPI = 140

DEFAULT_FIGSIZE = (
    12,
    6,
)


def configure_visuals() -> None:
    sns.set_theme(
        style=EDA_STYLE,
        context="notebook",
    )

    plt.rcParams[
        "figure.figsize"
    ] = DEFAULT_FIGSIZE

    plt.rcParams[
        "figure.dpi"
    ] = FIGURE_DPI

    plt.rcParams[
        "axes.titlesize"
    ] = 14

    plt.rcParams[
        "axes.labelsize"
    ] = 11


def dataframe_profile(
    dataframe: pd.DataFrame,
) -> dict:
    return {
        "Rows": len(
            dataframe
        ),
        "Columns": len(
            dataframe.columns
        ),
        "DuplicateRows": int(
            dataframe.duplicated().sum()
        ),
        "MissingCells": int(
            dataframe.isna().sum().sum()
        ),
        "MemoryMB": round(
            dataframe.memory_usage(
                deep=True
            ).sum()
            / 1024
            / 1024,
            2,
        ),
    }


def missing_value_report(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "Column",
                "MissingCount",
                "MissingPct",
            ]
        )

    missing = (
        dataframe.isna().sum()
    )

    report = pd.DataFrame(
        {
            "Column": (
                missing.index
            ),
            "MissingCount": (
                missing.values
            ),
        }
    )

    report[
        "MissingPct"
    ] = (
        report[
            "MissingCount"
        ]
        / len(
            dataframe
        )
        * 100
    )

    return (
        report.loc[
            report[
                "MissingCount"
            ]
            > 0
        ]
        .sort_values(
            [
                "MissingPct",
                "MissingCount",
            ],
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def numeric_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    numeric = (
        dataframe.select_dtypes(
            include="number"
        )
    )

    if numeric.empty:
        return pd.DataFrame()

    result = (
        numeric.describe(
            percentiles=[
                0.25,
                0.50,
                0.75,
                0.90,
                0.95,
                0.99,
            ]
        )
        .T
    )

    result[
        "Missing"
    ] = (
        numeric.isna().sum()
    )

    result[
        "Skewness"
    ] = (
        numeric.skew()
    )

    return result


def save_csv(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )


def save_figure(
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )

    plt.close()


def format_aed_axis(
    axis,
    axis_name: str = "y",
) -> None:
    from matplotlib.ticker import (
        FuncFormatter,
    )

    formatter = FuncFormatter(
        lambda value, _:
            (
                f"AED "
                f"{value / 1_000_000:.1f}M"
                if abs(value)
                >= 1_000_000
                else
                (
                    f"AED "
                    f"{value / 1_000:.1f}K"
                    if abs(value)
                    >= 1_000
                    else
                    f"AED {value:,.0f}"
                )
            )
    )

    if axis_name == "x":
        axis.xaxis.set_major_formatter(
            formatter
        )
    else:
        axis.yaxis.set_major_formatter(
            formatter
        )