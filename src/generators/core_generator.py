"""
Generation of core/reference datasets.

This module does not connect to SQL Server.
It only generates validated Pandas DataFrames.
"""

import numpy as np
import pandas as pd

from config.generation_config import CONFIG
from src.generators.uae_calendar import (
    apply_uae_calendar,
    validate_uae_calendar,
)


EMIRATES = [
    ("AUH", "Abu Dhabi"),
    ("DXB", "Dubai"),
    ("SHJ", "Sharjah"),
    ("AJM", "Ajman"),
    ("UAQ", "Umm Al Quwain"),
    ("RAK", "Ras Al Khaimah"),
    ("FUJ", "Fujairah"),
]


CITIES = {
    "Abu Dhabi": [
        "Abu Dhabi",
        "Al Ain",
    ],
    "Dubai": [
        "Dubai",
    ],
    "Sharjah": [
        "Sharjah",
        "Khor Fakkan",
        "Kalba",
    ],
    "Ajman": [
        "Ajman",
    ],
    "Umm Al Quwain": [
        "Umm Al Quwain",
    ],
    "Ras Al Khaimah": [
        "Ras Al Khaimah",
    ],
    "Fujairah": [
        "Fujairah",
    ],
}


STORE_DISTRIBUTION = {
    "Abu Dhabi": 6,
    "Dubai": 7,
    "Sharjah": 4,
    "Ajman": 2,
    "Umm Al Quwain": 1,
    "Ras Al Khaimah": 3,
    "Fujairah": 2,
}


SALES_CHANNELS = [
    ("STORE", "Physical Store"),
    ("ONLINE", "Online"),
]


PAYMENT_METHODS = [
    ("CASH", "Cash"),
    ("CREDIT_CARD", "Credit Card"),
    ("DEBIT_CARD", "Debit Card"),
    ("DIGITAL_WALLET", "Digital Wallet"),
]


STORE_TYPES = [
    "MALL",
    "HIGH_STREET",
    "COMMUNITY",
]

STORE_TYPE_PROBABILITIES = [
    0.60,
    0.20,
    0.20,
]


def generate_emirates() -> pd.DataFrame:
    df = pd.DataFrame(
        EMIRATES,
        columns=[
            "EmirateCode",
            "EmirateName",
        ],
    )

    df.insert(
        0,
        "EmirateId",
        range(1, len(df) + 1),
    )

    df["IsActive"] = 1

    return df


def generate_cities(
    emirates: pd.DataFrame,
) -> pd.DataFrame:
    emirate_lookup = dict(
        zip(
            emirates["EmirateName"],
            emirates["EmirateId"],
        )
    )

    rows = []
    city_id = 1

    for emirate_name, city_names in CITIES.items():
        emirate_id = emirate_lookup[emirate_name]

        for city_name in city_names:
            rows.append(
                {
                    "CityId": city_id,
                    "EmirateId": emirate_id,
                    "CityName": city_name,
                    "IsActive": 1,
                }
            )
            city_id += 1

    return pd.DataFrame(rows)


def generate_sales_channels() -> pd.DataFrame:
    df = pd.DataFrame(
        SALES_CHANNELS,
        columns=[
            "ChannelCode",
            "ChannelName",
        ],
    )

    df.insert(
        0,
        "SalesChannelId",
        range(1, len(df) + 1),
    )

    df["IsActive"] = 1

    return df


def generate_payment_methods() -> pd.DataFrame:
    df = pd.DataFrame(
        PAYMENT_METHODS,
        columns=[
            "PaymentMethodCode",
            "PaymentMethodName",
        ],
    )

    df.insert(
        0,
        "PaymentMethodId",
        range(1, len(df) + 1),
    )

    df["IsActive"] = 1

    return df


def generate_date_dimension() -> pd.DataFrame:
    dates = pd.date_range(
        start=CONFIG.start_date,
        end=CONFIG.end_date,
        freq="D",
    )

    df = pd.DataFrame(
        {
            "FullDate": dates,
        }
    )

    df["FullDate"] = df["FullDate"].dt.date

    df["DateKey"] = (
        pd.to_datetime(df["FullDate"])
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    datetime_series = pd.to_datetime(
        df["FullDate"]
    )

    df["DayNumber"] = datetime_series.dt.day

    df["DayName"] = datetime_series.dt.day_name()

    # ISO convention:
    # Monday = 1
    # Sunday = 7
    df["DayOfWeekNumber"] = (
        datetime_series.dt.dayofweek + 1
    )

    df["WeekOfYear"] = (
        datetime_series
        .dt
        .isocalendar()
        .week
        .astype(int)
    )

    df["MonthNumber"] = datetime_series.dt.month
    df["MonthName"] = datetime_series.dt.month_name()
    df["QuarterNumber"] = datetime_series.dt.quarter
    df["YearNumber"] = datetime_series.dt.year

    # Saturday and Sunday are used as the weekend
    # convention throughout the simulation.
    df["IsWeekend"] = (
        df["DayOfWeekNumber"].isin([6, 7])
    ).astype(int)

    df = apply_uae_calendar(df)

    validate_uae_calendar(df)

    columns = [
        "DateKey",
        "FullDate",
        "DayNumber",
        "DayName",
        "DayOfWeekNumber",
        "WeekOfYear",
        "MonthNumber",
        "MonthName",
        "QuarterNumber",
        "YearNumber",
        "IsWeekend",
        "IsRamadan",
        "IsEidAlFitr",
        "IsEidAlAdha",
        "IsWhiteFriday",
        "IsEidAlEtihad",
        "IsSummer",
        "IsYearEndSeason",
    ]

    return df[columns]


def generate_stores(
    cities: pd.DataFrame,
    emirates: pd.DataFrame,
) -> pd.DataFrame:
    rng = np.random.default_rng(
        CONFIG.random_seed
    )

    city_data = cities.merge(
        emirates[
            [
                "EmirateId",
                "EmirateName",
            ]
        ],
        on="EmirateId",
        how="left",
        validate="many_to_one",
    )

    rows = []
    store_id = 1

    for (
        emirate_name,
        store_count,
    ) in STORE_DISTRIBUTION.items():

        eligible_cities = city_data.loc[
            city_data["EmirateName"]
            == emirate_name,
            [
                "CityId",
                "CityName",
            ],
        ]

        if eligible_cities.empty:
            raise ValueError(
                "No eligible cities for "
                f"{emirate_name}."
            )

        for emirate_store_number in range(
            1,
            store_count + 1,
        ):
            selected_index = int(
                rng.integers(
                    0,
                    len(eligible_cities),
                )
            )

            selected_city = (
                eligible_cities
                .iloc[selected_index]
            )

            store_type = rng.choice(
                STORE_TYPES,
                p=STORE_TYPE_PROBABILITIES,
            )

            open_date = (
                pd.Timestamp("2014-01-01")
                + pd.to_timedelta(
                    int(
                        rng.integers(
                            0,
                            365 * 9,
                        )
                    ),
                    unit="D",
                )
            ).date()

            floor_area = round(
                float(
                    rng.uniform(
                        350,
                        2500,
                    )
                ),
                2,
            )

            rows.append(
                {
                    "StoreId": store_id,
                    "CityId": int(
                        selected_city["CityId"]
                    ),
                    "StoreCode": (
                        f"STR{store_id:03d}"
                    ),
                    "StoreName": (
                        f"{emirate_name} "
                        f"Store "
                        f"{emirate_store_number:02d}"
                    ),
                    "OpenDate": open_date,
                    "StoreType": store_type,
                    "FloorAreaSqM": floor_area,
                    "IsActive": 1,
                }
            )

            store_id += 1

    return pd.DataFrame(rows)


def validate_core_data(
    datasets: dict[str, pd.DataFrame],
) -> None:
    emirates = datasets["emirates"]
    cities = datasets["cities"]
    stores = datasets["stores"]
    dates = datasets["date_dimension"]
    channels = datasets["sales_channels"]
    payment_methods = datasets["payment_methods"]

    if len(emirates) != 7:
        raise ValueError(
            "Exactly 7 emirates are required."
        )

    if len(stores) != CONFIG.number_of_stores:
        raise ValueError(
            "Incorrect number of stores."
        )

    if len(dates) != 1096:
        raise ValueError(
            "2023-2025 must contain 1,096 dates."
        )

    if len(channels) != 2:
        raise ValueError(
            "Expected exactly 2 sales channels."
        )

    if len(payment_methods) != 4:
        raise ValueError(
            "Expected exactly 4 payment methods."
        )

    primary_keys = {
        "emirates": "EmirateId",
        "cities": "CityId",
        "stores": "StoreId",
        "date_dimension": "DateKey",
        "sales_channels": "SalesChannelId",
        "payment_methods": "PaymentMethodId",
    }

    for dataset_name, primary_key in (
        primary_keys.items()
    ):
        df = datasets[dataset_name]

        if df[primary_key].isna().any():
            raise ValueError(
                f"{dataset_name}: null PK."
            )

        if not df[primary_key].is_unique:
            raise ValueError(
                f"{dataset_name}: duplicate PK."
            )

    if not cities["EmirateId"].isin(
        emirates["EmirateId"]
    ).all():
        raise ValueError(
            "Orphan City.EmirateId detected."
        )

    if not stores["CityId"].isin(
        cities["CityId"]
    ).all():
        raise ValueError(
            "Orphan Store.CityId detected."
        )

    if (
        stores["StoreCode"]
        .duplicated()
        .any()
    ):
        raise ValueError(
            "Duplicate StoreCode detected."
        )

    if dates["FullDate"].min() != CONFIG.start_date:
        raise ValueError(
            "Invalid minimum calendar date."
        )

    if dates["FullDate"].max() != CONFIG.end_date:
        raise ValueError(
            "Invalid maximum calendar date."
        )


def generate_core_datasets() -> dict[str, pd.DataFrame]:
    emirates = generate_emirates()

    cities = generate_cities(
        emirates=emirates,
    )

    stores = generate_stores(
        cities=cities,
        emirates=emirates,
    )

    datasets = {
        "emirates": emirates,
        "cities": cities,
        "stores": stores,
        "date_dimension": generate_date_dimension(),
        "sales_channels": generate_sales_channels(),
        "payment_methods": generate_payment_methods(),
    }

    validate_core_data(datasets)

    return datasets