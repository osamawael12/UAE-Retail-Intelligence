"""
UAE retail calendar rules used by the synthetic simulation.

Lunar-event ranges are explicit simulation assumptions.
They are designed for retail seasonality modelling and are
not intended to act as an official religious calendar.
"""

from datetime import date

import pandas as pd


EVENT_RANGES = {
    2023: {
        "ramadan": (
            date(2023, 3, 23),
            date(2023, 4, 20),
        ),
        "eid_al_fitr": (
            date(2023, 4, 21),
            date(2023, 4, 23),
        ),
        "eid_al_adha": (
            date(2023, 6, 28),
            date(2023, 6, 30),
        ),
        "white_friday": (
            date(2023, 11, 20),
            date(2023, 11, 26),
        ),
        "eid_al_etihad": (
            date(2023, 12, 2),
            date(2023, 12, 3),
        ),
    },
    2024: {
        "ramadan": (
            date(2024, 3, 11),
            date(2024, 4, 9),
        ),
        "eid_al_fitr": (
            date(2024, 4, 10),
            date(2024, 4, 12),
        ),
        "eid_al_adha": (
            date(2024, 6, 16),
            date(2024, 6, 18),
        ),
        "white_friday": (
            date(2024, 11, 25),
            date(2024, 12, 1),
        ),
        "eid_al_etihad": (
            date(2024, 12, 2),
            date(2024, 12, 3),
        ),
    },
    2025: {
        "ramadan": (
            date(2025, 3, 1),
            date(2025, 3, 29),
        ),
        "eid_al_fitr": (
            date(2025, 3, 30),
            date(2025, 4, 1),
        ),
        "eid_al_adha": (
            date(2025, 6, 6),
            date(2025, 6, 8),
        ),
        "white_friday": (
            date(2025, 11, 24),
            date(2025, 11, 30),
        ),
        "eid_al_etihad": (
            date(2025, 12, 2),
            date(2025, 12, 3),
        ),
    },
}


EVENT_COLUMN_MAPPING = {
    "ramadan": "IsRamadan",
    "eid_al_fitr": "IsEidAlFitr",
    "eid_al_adha": "IsEidAlAdha",
    "white_friday": "IsWhiteFriday",
    "eid_al_etihad": "IsEidAlEtihad",
}


def apply_uae_calendar(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = dataframe.copy()

    for column in EVENT_COLUMN_MAPPING.values():
        df[column] = 0

    for year, events in EVENT_RANGES.items():
        year_mask = df["YearNumber"] == year

        for event_name, column_name in (
            EVENT_COLUMN_MAPPING.items()
        ):
            start_date, end_date = events[event_name]

            event_mask = (
                year_mask
                & (df["FullDate"] >= start_date)
                & (df["FullDate"] <= end_date)
            )

            df.loc[event_mask, column_name] = 1

    # June through August.
    df["IsSummer"] = (
        df["MonthNumber"].isin([6, 7, 8])
    ).astype(int)

    # December 15 through December 31.
    df["IsYearEndSeason"] = (
        (df["MonthNumber"] == 12)
        & (df["DayNumber"] >= 15)
    ).astype(int)

    return df


def validate_uae_calendar(
    dataframe: pd.DataFrame,
) -> None:
    columns = [
        *EVENT_COLUMN_MAPPING.values(),
        "IsSummer",
        "IsYearEndSeason",
    ]

    for column in columns:
        if column not in dataframe.columns:
            raise ValueError(
                f"Missing calendar column: {column}"
            )

        if not dataframe[column].isin([0, 1]).all():
            raise ValueError(
                f"Invalid binary values in {column}."
            )

    for year in EVENT_RANGES:
        year_data = dataframe[
            dataframe["YearNumber"] == year
        ]

        for column in EVENT_COLUMN_MAPPING.values():
            if year_data[column].sum() == 0:
                raise ValueError(
                    f"{column} has no dates for {year}."
                )

    invalid_overlap = (
        (dataframe["IsRamadan"] == 1)
        & (
            (dataframe["IsEidAlFitr"] == 1)
            | (dataframe["IsEidAlAdha"] == 1)
        )
    )

    if invalid_overlap.any():
        raise ValueError(
            "Ramadan overlaps with an Eid range."
        )