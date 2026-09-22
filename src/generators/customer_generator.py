"""
Synthetic customer data generator.

Generates:
1. Customer master data for SQL Server.
2. Customer segment history.
3. Hidden simulation profiles used by later generators.

This module does not connect to SQL Server.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


# ============================================================
# Customer Personas
# ============================================================

PERSONA_CONFIG = {
    "VIP": {
        "weight": 0.05,
        "purchase_propensity": (0.80, 1.00),
        "price_sensitivity": (0.05, 0.25),
        "promotion_sensitivity": (0.10, 0.35),
        "return_multiplier": (0.80, 1.10),
        "basket_size": (3.5, 6.0),
    },
    "LOYAL": {
        "weight": 0.20,
        "purchase_propensity": (0.60, 0.85),
        "price_sensitivity": (0.20, 0.45),
        "promotion_sensitivity": (0.25, 0.50),
        "return_multiplier": (0.75, 1.00),
        "basket_size": (2.8, 4.5),
    },
    "REGULAR": {
        "weight": 0.45,
        "purchase_propensity": (0.30, 0.65),
        "price_sensitivity": (0.35, 0.65),
        "promotion_sensitivity": (0.35, 0.65),
        "return_multiplier": (0.90, 1.15),
        "basket_size": (1.8, 3.5),
    },
    "DISCOUNT_SEEKER": {
        "weight": 0.20,
        "purchase_propensity": (0.20, 0.55),
        "price_sensitivity": (0.70, 1.00),
        "promotion_sensitivity": (0.75, 1.00),
        "return_multiplier": (1.00, 1.30),
        "basket_size": (1.5, 3.2),
    },
    "AT_RISK": {
        "weight": 0.10,
        "purchase_propensity": (0.05, 0.25),
        "price_sensitivity": (0.40, 0.75),
        "promotion_sensitivity": (0.40, 0.75),
        "return_multiplier": (1.00, 1.35),
        "basket_size": (1.2, 2.5),
    },
}


PREFERRED_CATEGORY_WEIGHTS = {
    "Fashion": 0.18,
    "Electronics": 0.14,
    "Beauty": 0.14,
    "Home": 0.13,
    "Sports": 0.11,
    "Grocery": 0.12,
    "Toys": 0.08,
    "Lifestyle": 0.10,
}


NATIONALITIES = [
    "UAE",
    "India",
    "Pakistan",
    "Egypt",
    "Philippines",
    "Jordan",
    "Lebanon",
    "United Kingdom",
    "Bangladesh",
    "Saudi Arabia",
    "Other",
]


NATIONALITY_WEIGHTS = [
    0.22,
    0.20,
    0.10,
    0.09,
    0.09,
    0.05,
    0.04,
    0.04,
    0.04,
    0.03,
    0.10,
]


FIRST_NAMES_MALE = [
    "Ahmed",
    "Mohammed",
    "Omar",
    "Ali",
    "Youssef",
    "Khalid",
    "Saeed",
    "Hassan",
    "Ibrahim",
    "Adam",
    "Daniel",
    "John",
    "Arjun",
    "Rahul",
    "Ravi",
    "Imran",
    "Bilal",
    "Samir",
    "Karim",
    "Faisal",
]


FIRST_NAMES_FEMALE = [
    "Fatima",
    "Aisha",
    "Mariam",
    "Sara",
    "Noor",
    "Layla",
    "Huda",
    "Amal",
    "Reem",
    "Hana",
    "Anna",
    "Maria",
    "Priya",
    "Ananya",
    "Meera",
    "Nadia",
    "Rania",
    "Dina",
    "Lina",
    "Zainab",
]


LAST_NAMES = [
    "Al Mansoori",
    "Al Mazrouei",
    "Al Nuaimi",
    "Al Shamsi",
    "Al Hammadi",
    "Khan",
    "Ahmed",
    "Ali",
    "Hassan",
    "Sharma",
    "Patel",
    "Singh",
    "Thomas",
    "George",
    "Rahman",
    "Santos",
    "Garcia",
    "Smith",
    "Brown",
    "Wilson",
]


# ============================================================
# Helpers
# ============================================================

def _probability(value: float) -> float:
    return round(float(value), 6)


def _random_date(
    rng: np.random.Generator,
    start_date: date,
    end_date: date,
) -> date:
    days = (end_date - start_date).days

    if days < 0:
        raise ValueError(
            "start_date cannot be after end_date."
        )

    offset = int(
        rng.integers(
            0,
            days + 1,
        )
    )

    return (
        start_date
        + timedelta(days=offset)
    )


def _generate_birth_date(
    rng: np.random.Generator,
    reference_date: date,
) -> date:
    age = int(
        rng.integers(
            CONFIG.minimum_customer_age,
            CONFIG.maximum_customer_age + 1,
        )
    )

    additional_days = int(
        rng.integers(
            0,
            365,
        )
    )

    return (
        reference_date
        - timedelta(
            days=age * 365
            + additional_days
        )
    )


# ============================================================
# Main Customer Generation
# ============================================================

def generate_customer_datasets(
    emirates: pd.DataFrame,
    sales_channels: pd.DataFrame,
    categories: pd.DataFrame,
) -> dict[str, pd.DataFrame]:

    rng = np.random.default_rng(
        CONFIG.random_seed + 400
    )

    persona_names = list(
        PERSONA_CONFIG.keys()
    )

    persona_weights = [
        PERSONA_CONFIG[name]["weight"]
        for name in persona_names
    ]

    category_names = list(
        PREFERRED_CATEGORY_WEIGHTS.keys()
    )

    category_weights = [
        PREFERRED_CATEGORY_WEIGHTS[name]
        for name in category_names
    ]

    store_channel_id = int(
        sales_channels.loc[
            sales_channels["ChannelCode"]
            == "STORE",
            "SalesChannelId",
        ].iloc[0]
    )

    online_channel_id = int(
        sales_channels.loc[
            sales_channels["ChannelCode"]
            == "ONLINE",
            "SalesChannelId",
        ].iloc[0]
    )

    emirate_ids = (
        emirates["EmirateId"]
        .to_numpy()
    )

    category_lookup = dict(
        zip(
            categories["CategoryName"],
            categories["CategoryId"],
        )
    )

    customer_rows = []
    profile_rows = []
    segment_rows = []

    for customer_id in range(
        1,
        CONFIG.number_of_customers + 1,
    ):
        registration_date = (
            _random_date(
                rng=rng,
                start_date=date(
                    2019,
                    1,
                    1,
                ),
                end_date=CONFIG.end_date,
            )
        )

        persona = str(
            rng.choice(
                persona_names,
                p=persona_weights,
            )
        )

        persona_config = (
            PERSONA_CONFIG[persona]
        )

        gender = str(
            rng.choice(
                [
                    "MALE",
                    "FEMALE",
                    "PREFER_NOT_TO_SAY",
                ],
                p=[
                    0.49,
                    0.49,
                    0.02,
                ],
            )
        )

        if gender == "MALE":
            first_name = str(
                rng.choice(
                    FIRST_NAMES_MALE
                )
            )
        elif gender == "FEMALE":
            first_name = str(
                rng.choice(
                    FIRST_NAMES_FEMALE
                )
            )
        else:
            combined_names = (
                FIRST_NAMES_MALE
                + FIRST_NAMES_FEMALE
            )

            first_name = str(
                rng.choice(
                    combined_names
                )
            )

        last_name = str(
            rng.choice(
                LAST_NAMES
            )
        )

        birth_date = (
            _generate_birth_date(
                rng=rng,
                reference_date=(
                    registration_date
                ),
            )
        )

        nationality = str(
            rng.choice(
                NATIONALITIES,
                p=NATIONALITY_WEIGHTS,
            )
        )

        preferred_emirate_id = int(
            rng.choice(
                emirate_ids
            )
        )

        # Persona affects channel preference.
        if persona in {
            "VIP",
            "DISCOUNT_SEEKER",
        }:
            online_probability = 0.48
        elif persona == "AT_RISK":
            online_probability = 0.38
        else:
            online_probability = 0.32

        preferred_channel_id = (
            online_channel_id
            if rng.random()
            < online_probability
            else store_channel_id
        )

        preferred_category_name = str(
            rng.choice(
                category_names,
                p=category_weights,
            )
        )

        preferred_category_id = int(
            category_lookup[
                preferred_category_name
            ]
        )

        purchase_min, purchase_max = (
            persona_config[
                "purchase_propensity"
            ]
        )

        purchase_propensity = (
            rng.uniform(
                purchase_min,
                purchase_max,
            )
        )

        price_min, price_max = (
            persona_config[
                "price_sensitivity"
            ]
        )

        price_sensitivity = (
            rng.uniform(
                price_min,
                price_max,
            )
        )

        promotion_min, promotion_max = (
            persona_config[
                "promotion_sensitivity"
            ]
        )

        promotion_sensitivity = (
            rng.uniform(
                promotion_min,
                promotion_max,
            )
        )

        return_min, return_max = (
            persona_config[
                "return_multiplier"
            ]
        )

        return_multiplier = (
            rng.uniform(
                return_min,
                return_max,
            )
        )

        basket_min, basket_max = (
            persona_config[
                "basket_size"
            ]
        )

        expected_basket_size = (
            rng.uniform(
                basket_min,
                basket_max,
            )
        )

        customer_code = (
            f"CUS{customer_id:07d}"
        )

        customer_rows.append(
            {
                "CustomerId": customer_id,
                "CustomerCode": (
                    customer_code
                ),
                "FirstName": first_name,
                "LastName": last_name,
                "Gender": gender,
                "DateOfBirth": birth_date,
                "Email": (
                    f"customer"
                    f"{customer_id:07d}"
                    "@synthetic-retail.ae"
                ),
                "Phone": (
                    f"+97150"
                    f"{customer_id:07d}"
                ),
                "Nationality": nationality,
                "RegistrationDate": (
                    registration_date
                ),
                "PreferredEmirateId": (
                    preferred_emirate_id
                ),
                "PreferredChannelId": (
                    preferred_channel_id
                ),
                "IsActive": (
                    0
                    if persona
                    == "AT_RISK"
                    and rng.random()
                    < 0.12
                    else 1
                ),
            }
        )

        segment_rows.append(
            {
                "CustomerSegmentHistoryId": (
                    customer_id
                ),
                "CustomerId": (
                    customer_id
                ),
                "SegmentName": persona,
                "EffectiveFrom": (
                    registration_date
                ),
                "EffectiveTo": None,
                "IsCurrent": 1,
            }
        )

        profile_rows.append(
            {
                "CustomerId": (
                    customer_id
                ),
                "Persona": persona,
                "PurchasePropensity": (
                    _probability(
                        purchase_propensity
                    )
                ),
                "PriceSensitivity": (
                    _probability(
                        price_sensitivity
                    )
                ),
                "PromotionSensitivity": (
                    _probability(
                        promotion_sensitivity
                    )
                ),
                "ReturnMultiplier": (
                    _probability(
                        return_multiplier
                    )
                ),
                "ExpectedBasketSize": (
                    round(
                        float(
                            expected_basket_size
                        ),
                        4,
                    )
                ),
                "PreferredCategoryId": (
                    preferred_category_id
                ),
            }
        )

    customers = pd.DataFrame(
        customer_rows
    )

    segment_history = pd.DataFrame(
        segment_rows
    )

    profiles = pd.DataFrame(
        profile_rows
    )

    datasets = {
        "customers": customers,
        "customer_segment_history": (
            segment_history
        ),
        "customer_simulation_profiles": (
            profiles
        ),
    }

    validate_customer_data(
        datasets=datasets,
        emirates=emirates,
        sales_channels=sales_channels,
        categories=categories,
    )

    return datasets


# ============================================================
# Validation
# ============================================================

def validate_customer_data(
    datasets: dict[str, pd.DataFrame],
    emirates: pd.DataFrame,
    sales_channels: pd.DataFrame,
    categories: pd.DataFrame,
) -> None:

    customers = datasets[
        "customers"
    ]

    segment_history = datasets[
        "customer_segment_history"
    ]

    profiles = datasets[
        "customer_simulation_profiles"
    ]

    expected = (
        CONFIG.number_of_customers
    )

    if len(customers) != expected:
        raise ValueError(
            "Incorrect customer count."
        )

    if len(segment_history) != expected:
        raise ValueError(
            "Incorrect segment-history count."
        )

    if len(profiles) != expected:
        raise ValueError(
            "Incorrect simulation-profile count."
        )

    unique_columns = [
        "CustomerId",
        "CustomerCode",
        "Email",
    ]

    for column in unique_columns:
        if not customers[
            column
        ].is_unique:
            raise ValueError(
                f"Duplicate customer "
                f"{column}."
            )

    if customers[
        "CustomerId"
    ].isna().any():
        raise ValueError(
            "CustomerId contains nulls."
        )

    if not customers[
        "PreferredEmirateId"
    ].isin(
        emirates["EmirateId"]
    ).all():
        raise ValueError(
            "Invalid PreferredEmirateId."
        )

    if not customers[
        "PreferredChannelId"
    ].isin(
        sales_channels[
            "SalesChannelId"
        ]
    ).all():
        raise ValueError(
            "Invalid PreferredChannelId."
        )

    if not segment_history[
        "CustomerId"
    ].isin(
        customers["CustomerId"]
    ).all():
        raise ValueError(
            "Orphan customer segment."
        )

    if not profiles[
        "CustomerId"
    ].isin(
        customers["CustomerId"]
    ).all():
        raise ValueError(
            "Orphan simulation profile."
        )

    if not profiles[
        "PreferredCategoryId"
    ].isin(
        categories[
            "CategoryId"
        ]
    ).all():
        raise ValueError(
            "Invalid PreferredCategoryId."
        )

    if not segment_history[
        "SegmentName"
    ].isin(
        PERSONA_CONFIG.keys()
    ).all():
        raise ValueError(
            "Invalid customer persona."
        )

    probability_columns = [
        "PurchasePropensity",
        "PriceSensitivity",
        "PromotionSensitivity",
    ]

    for column in probability_columns:
        if not profiles[
            column
        ].between(
            0,
            1,
        ).all():
            raise ValueError(
                f"Invalid {column}."
            )

    if (
        profiles["ReturnMultiplier"]
        <= 0
    ).any():
        raise ValueError(
            "ReturnMultiplier must be "
            "positive."
        )

    if (
        profiles["ExpectedBasketSize"]
        < 1
    ).any():
        raise ValueError(
            "Invalid ExpectedBasketSize."
        )

    today_limit = (
        CONFIG.end_date
    )

    if (
        customers["RegistrationDate"]
        > today_limit
    ).any():
        raise ValueError(
            "Customer registered after "
            "simulation period."
        )

    if (
        customers["DateOfBirth"]
        >= customers[
            "RegistrationDate"
        ]
    ).any():
        raise ValueError(
            "Invalid customer birth date."
        )

    if not customers[
        "IsActive"
    ].isin([0, 1]).all():
        raise ValueError(
            "Invalid IsActive value."
        )

    current_counts = (
        segment_history.loc[
            segment_history["IsCurrent"]
            == 1
        ]
        .groupby("CustomerId")
        .size()
    )

    if len(current_counts) != expected:
        raise ValueError(
            "Every customer must have "
            "one current segment."
        )

    if not (
        current_counts == 1
    ).all():
        raise ValueError(
            "Customer has multiple "
            "current segments."
        )