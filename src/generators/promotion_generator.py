"""
Synthetic promotion generator.

Generates:
- Promotion
- PromotionProduct
- PromotionCategory
- PromotionStore

Promotions are designed to influence the later sales simulation.

Promotion semantics:
- SEASONAL: applies broadly unless targeting bridges exist.
- CATEGORY: targets selected categories.
- PRODUCT: targets selected products.
- STORE: targets selected stores.

DiscountValue representation:
- PERCENTAGE: 10 means 10%
- FIXED_AMOUNT: value is AED

This module does not connect to SQL Server.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


# ============================================================
# Fixed UAE retail campaigns
# ============================================================

SEASONAL_CAMPAIGNS = {
    2023: [
        {
            "name": "Ramadan",
            "start": date(2023, 3, 23),
            "end": date(2023, 4, 20),
            "discount_range": (8, 18),
        },
        {
            "name": "Eid Al Fitr",
            "start": date(2023, 4, 21),
            "end": date(2023, 4, 23),
            "discount_range": (10, 22),
        },
        {
            "name": "Summer",
            "start": date(2023, 6, 15),
            "end": date(2023, 8, 31),
            "discount_range": (8, 20),
        },
        {
            "name": "Eid Al Adha",
            "start": date(2023, 6, 28),
            "end": date(2023, 6, 30),
            "discount_range": (10, 22),
        },
        {
            "name": "White Friday",
            "start": date(2023, 11, 20),
            "end": date(2023, 11, 26),
            "discount_range": (18, 35),
        },
        {
            "name": "Eid Al Etihad",
            "start": date(2023, 12, 2),
            "end": date(2023, 12, 3),
            "discount_range": (10, 20),
        },
        {
            "name": "Year End",
            "start": date(2023, 12, 15),
            "end": date(2023, 12, 31),
            "discount_range": (12, 25),
        },
    ],
    2024: [
        {
            "name": "Ramadan",
            "start": date(2024, 3, 11),
            "end": date(2024, 4, 9),
            "discount_range": (8, 18),
        },
        {
            "name": "Eid Al Fitr",
            "start": date(2024, 4, 10),
            "end": date(2024, 4, 12),
            "discount_range": (10, 22),
        },
        {
            "name": "Summer",
            "start": date(2024, 6, 15),
            "end": date(2024, 8, 31),
            "discount_range": (8, 20),
        },
        {
            "name": "Eid Al Adha",
            "start": date(2024, 6, 16),
            "end": date(2024, 6, 18),
            "discount_range": (10, 22),
        },
        {
            "name": "White Friday",
            "start": date(2024, 11, 25),
            "end": date(2024, 12, 1),
            "discount_range": (18, 35),
        },
        {
            "name": "Eid Al Etihad",
            "start": date(2024, 12, 2),
            "end": date(2024, 12, 3),
            "discount_range": (10, 20),
        },
        {
            "name": "Year End",
            "start": date(2024, 12, 15),
            "end": date(2024, 12, 31),
            "discount_range": (12, 25),
        },
    ],
    2025: [
        {
            "name": "Ramadan",
            "start": date(2025, 3, 1),
            "end": date(2025, 3, 29),
            "discount_range": (8, 18),
        },
        {
            "name": "Eid Al Fitr",
            "start": date(2025, 3, 30),
            "end": date(2025, 4, 1),
            "discount_range": (10, 22),
        },
        {
            "name": "Summer",
            "start": date(2025, 6, 15),
            "end": date(2025, 8, 31),
            "discount_range": (8, 20),
        },
        {
            "name": "Eid Al Adha",
            "start": date(2025, 6, 6),
            "end": date(2025, 6, 8),
            "discount_range": (10, 22),
        },
        {
            "name": "White Friday",
            "start": date(2025, 11, 24),
            "end": date(2025, 11, 30),
            "discount_range": (18, 35),
        },
        {
            "name": "Eid Al Etihad",
            "start": date(2025, 12, 2),
            "end": date(2025, 12, 3),
            "discount_range": (10, 20),
        },
        {
            "name": "Year End",
            "start": date(2025, 12, 15),
            "end": date(2025, 12, 31),
            "discount_range": (12, 25),
        },
    ],
}


# ============================================================
# Helper functions
# ============================================================

def _random_date_range(
    rng: np.random.Generator,
    year: int,
    minimum_days: int,
    maximum_days: int,
) -> tuple[date, date]:
    """
    Generate a promotion date range fully contained
    within the specified year.
    """

    year_start = max(
        date(year, 1, 1),
        CONFIG.start_date,
    )

    year_end = min(
        date(year, 12, 31),
        CONFIG.end_date,
    )

    duration = int(
        rng.integers(
            minimum_days,
            maximum_days + 1,
        )
    )

    latest_start = (
        year_end
        - timedelta(
            days=duration - 1
        )
    )

    total_start_days = (
        latest_start
        - year_start
    ).days

    offset = int(
        rng.integers(
            0,
            total_start_days + 1,
        )
    )

    start_date = (
        year_start
        + timedelta(days=offset)
    )

    end_date = (
        start_date
        + timedelta(
            days=duration - 1
        )
    )

    return (
        start_date,
        end_date,
    )


def _percentage_discount(
    rng: np.random.Generator,
    minimum: float,
    maximum: float,
) -> float:
    return round(
        float(
            rng.uniform(
                minimum,
                maximum,
            )
        ),
        2,
    )


# ============================================================
# Promotion Generator
# ============================================================

def generate_promotion_datasets(
    categories: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Generate all promotion-related datasets.
    """

    rng = np.random.default_rng(
        CONFIG.random_seed + 600
    )

    promotion_rows = []
    promotion_product_rows = []
    promotion_category_rows = []
    promotion_store_rows = []

    promotion_id = 1

    # ========================================================
    # 1. Seasonal company-wide promotions
    # ========================================================

    for year in range(
        CONFIG.start_date.year,
        CONFIG.end_date.year + 1,
    ):
        campaigns = (
            SEASONAL_CAMPAIGNS[year]
        )

        for campaign_number, campaign in enumerate(
            campaigns,
            start=1,
        ):
            discount_min, discount_max = (
                campaign[
                    "discount_range"
                ]
            )

            discount_value = (
                _percentage_discount(
                    rng=rng,
                    minimum=discount_min,
                    maximum=discount_max,
                )
            )

            promotion_rows.append(
                {
                    "PromotionId": (
                        promotion_id
                    ),
                    "PromotionCode": (
                        f"SEA-{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionName": (
                        f"{campaign['name']} "
                        f"{year}"
                    ),
                    "PromotionType": (
                        "SEASONAL"
                    ),
                    "DiscountType": (
                        "PERCENTAGE"
                    ),
                    "DiscountValue": (
                        discount_value
                    ),
                    "StartDate": (
                        campaign["start"]
                    ),
                    "EndDate": (
                        campaign["end"]
                    ),
                    "IsActive": 1,
                }
            )

            # No bridge row means the seasonal campaign
            # is company-wide. The Sales Engine will use
            # this explicit rule.

            promotion_id += 1

    # ========================================================
    # 2. Category-specific promotions
    # ========================================================

    category_ids = (
        categories["CategoryId"]
        .astype(int)
        .to_numpy()
    )

    for year in range(
        CONFIG.start_date.year,
        CONFIG.end_date.year + 1,
    ):
        for campaign_number in range(
            1,
            7,
        ):
            start_date, end_date = (
                _random_date_range(
                    rng=rng,
                    year=year,
                    minimum_days=7,
                    maximum_days=21,
                )
            )

            selected_count = int(
                rng.choice(
                    [1, 2],
                    p=[
                        0.75,
                        0.25,
                    ],
                )
            )

            selected_categories = (
                rng.choice(
                    category_ids,
                    size=selected_count,
                    replace=False,
                )
            )

            discount_value = (
                _percentage_discount(
                    rng=rng,
                    minimum=8,
                    maximum=24,
                )
            )

            current_promotion_id = (
                promotion_id
            )

            promotion_rows.append(
                {
                    "PromotionId": (
                        current_promotion_id
                    ),
                    "PromotionCode": (
                        f"CAT-{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionName": (
                        f"Category Campaign "
                        f"{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionType": (
                        "CATEGORY"
                    ),
                    "DiscountType": (
                        "PERCENTAGE"
                    ),
                    "DiscountValue": (
                        discount_value
                    ),
                    "StartDate": (
                        start_date
                    ),
                    "EndDate": (
                        end_date
                    ),
                    "IsActive": 1,
                }
            )

            for category_id_raw in (
                selected_categories
            ):
                promotion_category_rows.append(
                    {
                        "PromotionId": (
                            current_promotion_id
                        ),
                        "CategoryId": int(
                            category_id_raw
                        ),
                    }
                )

            promotion_id += 1

    # ========================================================
    # 3. Product-specific promotions
    # ========================================================

    product_ids = (
        products["ProductId"]
        .astype(int)
        .to_numpy()
    )

    for year in range(
        CONFIG.start_date.year,
        CONFIG.end_date.year + 1,
    ):
        for campaign_number in range(
            1,
            9,
        ):
            start_date, end_date = (
                _random_date_range(
                    rng=rng,
                    year=year,
                    minimum_days=4,
                    maximum_days=14,
                )
            )

            selected_count = int(
                rng.integers(
                    5,
                    21,
                )
            )

            selected_products = (
                rng.choice(
                    product_ids,
                    size=selected_count,
                    replace=False,
                )
            )

            discount_value = (
                _percentage_discount(
                    rng=rng,
                    minimum=6,
                    maximum=30,
                )
            )

            current_promotion_id = (
                promotion_id
            )

            promotion_rows.append(
                {
                    "PromotionId": (
                        current_promotion_id
                    ),
                    "PromotionCode": (
                        f"PRD-{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionName": (
                        f"Product Campaign "
                        f"{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionType": (
                        "PRODUCT"
                    ),
                    "DiscountType": (
                        "PERCENTAGE"
                    ),
                    "DiscountValue": (
                        discount_value
                    ),
                    "StartDate": (
                        start_date
                    ),
                    "EndDate": (
                        end_date
                    ),
                    "IsActive": 1,
                }
            )

            for product_id_raw in (
                selected_products
            ):
                promotion_product_rows.append(
                    {
                        "PromotionId": (
                            current_promotion_id
                        ),
                        "ProductId": int(
                            product_id_raw
                        ),
                    }
                )

            promotion_id += 1

    # ========================================================
    # 4. Store-specific promotions
    # ========================================================

    store_ids = (
        stores["StoreId"]
        .astype(int)
        .to_numpy()
    )

    for year in range(
        CONFIG.start_date.year,
        CONFIG.end_date.year + 1,
    ):
        for campaign_number in range(
            1,
            5,
        ):
            start_date, end_date = (
                _random_date_range(
                    rng=rng,
                    year=year,
                    minimum_days=5,
                    maximum_days=12,
                )
            )

            selected_count = int(
                rng.integers(
                    1,
                    5,
                )
            )

            selected_stores = (
                rng.choice(
                    store_ids,
                    size=selected_count,
                    replace=False,
                )
            )

            discount_value = (
                _percentage_discount(
                    rng=rng,
                    minimum=5,
                    maximum=18,
                )
            )

            current_promotion_id = (
                promotion_id
            )

            promotion_rows.append(
                {
                    "PromotionId": (
                        current_promotion_id
                    ),
                    "PromotionCode": (
                        f"STR-{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionName": (
                        f"Store Campaign "
                        f"{year}-"
                        f"{campaign_number:02d}"
                    ),
                    "PromotionType": (
                        "STORE"
                    ),
                    "DiscountType": (
                        "PERCENTAGE"
                    ),
                    "DiscountValue": (
                        discount_value
                    ),
                    "StartDate": (
                        start_date
                    ),
                    "EndDate": (
                        end_date
                    ),
                    "IsActive": 1,
                }
            )

            for store_id_raw in (
                selected_stores
            ):
                promotion_store_rows.append(
                    {
                        "PromotionId": (
                            current_promotion_id
                        ),
                        "StoreId": int(
                            store_id_raw
                        ),
                    }
                )

            promotion_id += 1

    promotions = pd.DataFrame(
        promotion_rows
    )

    promotion_products = pd.DataFrame(
        promotion_product_rows,
        columns=[
            "PromotionId",
            "ProductId",
        ],
    )

    promotion_categories = pd.DataFrame(
        promotion_category_rows,
        columns=[
            "PromotionId",
            "CategoryId",
        ],
    )

    promotion_stores = pd.DataFrame(
        promotion_store_rows,
        columns=[
            "PromotionId",
            "StoreId",
        ],
    )

    datasets = {
        "promotions": promotions,
        "promotion_products": (
            promotion_products
        ),
        "promotion_categories": (
            promotion_categories
        ),
        "promotion_stores": (
            promotion_stores
        ),
    }

    validate_promotion_data(
        datasets=datasets,
        categories=categories,
        products=products,
        stores=stores,
    )

    return datasets


# ============================================================
# Validation
# ============================================================

def validate_promotion_data(
    datasets: dict[str, pd.DataFrame],
    categories: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> None:
    """
    Validate promotion integrity and business rules.
    """

    promotions = datasets[
        "promotions"
    ]

    promotion_products = datasets[
        "promotion_products"
    ]

    promotion_categories = datasets[
        "promotion_categories"
    ]

    promotion_stores = datasets[
        "promotion_stores"
    ]

    if promotions.empty:
        raise ValueError(
            "No promotions generated."
        )

    if not promotions[
        "PromotionId"
    ].is_unique:
        raise ValueError(
            "Duplicate PromotionId."
        )

    if not promotions[
        "PromotionCode"
    ].is_unique:
        raise ValueError(
            "Duplicate PromotionCode."
        )

    valid_types = {
        "SEASONAL",
        "PRODUCT",
        "CATEGORY",
        "STORE",
    }

    if not promotions[
        "PromotionType"
    ].isin(
        valid_types
    ).all():
        raise ValueError(
            "Invalid PromotionType."
        )

    valid_discount_types = {
        "PERCENTAGE",
        "FIXED_AMOUNT",
    }

    if not promotions[
        "DiscountType"
    ].isin(
        valid_discount_types
    ).all():
        raise ValueError(
            "Invalid DiscountType."
        )

    if (
        promotions[
            "DiscountValue"
        ] < 0
    ).any():
        raise ValueError(
            "Negative promotion discount."
        )

    percentage_promotions = (
        promotions[
            promotions[
                "DiscountType"
            ]
            == "PERCENTAGE"
        ]
    )

    if (
        percentage_promotions[
            "DiscountValue"
        ] > 100
    ).any():
        raise ValueError(
            "Percentage discount "
            "exceeds 100%."
        )

    start_dates = pd.to_datetime(
        promotions["StartDate"]
    )

    end_dates = pd.to_datetime(
        promotions["EndDate"]
    )

    if (
        end_dates
        < start_dates
    ).any():
        raise ValueError(
            "Promotion ends before "
            "it starts."
        )

    if (
        start_dates.dt.date
        < CONFIG.start_date
    ).any():
        raise ValueError(
            "Promotion starts before "
            "simulation period."
        )

    if (
        end_dates.dt.date
        > CONFIG.end_date
    ).any():
        raise ValueError(
            "Promotion ends after "
            "simulation period."
        )

    promotion_ids = set(
        promotions[
            "PromotionId"
        ].astype(int)
    )

    bridge_frames = [
        promotion_products,
        promotion_categories,
        promotion_stores,
    ]

    for bridge in bridge_frames:
        if not set(
            bridge[
                "PromotionId"
            ].astype(int)
        ).issubset(
            promotion_ids
        ):
            raise ValueError(
                "Promotion bridge contains "
                "invalid PromotionId."
            )

    if not promotion_products[
        "ProductId"
    ].isin(
        products[
            "ProductId"
        ]
    ).all():
        raise ValueError(
            "Invalid ProductId in "
            "PromotionProduct."
        )

    if not promotion_categories[
        "CategoryId"
    ].isin(
        categories[
            "CategoryId"
        ]
    ).all():
        raise ValueError(
            "Invalid CategoryId in "
            "PromotionCategory."
        )

    if not promotion_stores[
        "StoreId"
    ].isin(
        stores[
            "StoreId"
        ]
    ).all():
        raise ValueError(
            "Invalid StoreId in "
            "PromotionStore."
        )

    duplicate_product_bridge = (
        promotion_products
        .duplicated(
            subset=[
                "PromotionId",
                "ProductId",
            ]
        )
        .any()
    )

    if duplicate_product_bridge:
        raise ValueError(
            "Duplicate PromotionProduct."
        )

    duplicate_category_bridge = (
        promotion_categories
        .duplicated(
            subset=[
                "PromotionId",
                "CategoryId",
            ]
        )
        .any()
    )

    if duplicate_category_bridge:
        raise ValueError(
            "Duplicate PromotionCategory."
        )

    duplicate_store_bridge = (
        promotion_stores
        .duplicated(
            subset=[
                "PromotionId",
                "StoreId",
            ]
        )
        .any()
    )

    if duplicate_store_bridge:
        raise ValueError(
            "Duplicate PromotionStore."
        )

    # --------------------------------------------------------
    # Every targeted promotion must have targeting records.
    # --------------------------------------------------------

    product_promotion_ids = set(
        promotions.loc[
            promotions[
                "PromotionType"
            ]
            == "PRODUCT",
            "PromotionId",
        ].astype(int)
    )

    category_promotion_ids = set(
        promotions.loc[
            promotions[
                "PromotionType"
            ]
            == "CATEGORY",
            "PromotionId",
        ].astype(int)
    )

    store_promotion_ids = set(
        promotions.loc[
            promotions[
                "PromotionType"
            ]
            == "STORE",
            "PromotionId",
        ].astype(int)
    )

    bridge_product_ids = set(
        promotion_products[
            "PromotionId"
        ].astype(int)
    )

    bridge_category_ids = set(
        promotion_categories[
            "PromotionId"
        ].astype(int)
    )

    bridge_store_ids = set(
        promotion_stores[
            "PromotionId"
        ].astype(int)
    )

    if not product_promotion_ids.issubset(
        bridge_product_ids
    ):
        raise ValueError(
            "A PRODUCT promotion has "
            "no products."
        )

    if not category_promotion_ids.issubset(
        bridge_category_ids
    ):
        raise ValueError(
            "A CATEGORY promotion has "
            "no categories."
        )

    if not store_promotion_ids.issubset(
        bridge_store_ids
    ):
        raise ValueError(
            "A STORE promotion has "
            "no stores."
        )

    # --------------------------------------------------------
    # Seasonal campaigns are intentionally global.
    # --------------------------------------------------------

    seasonal_ids = set(
        promotions.loc[
            promotions[
                "PromotionType"
            ]
            == "SEASONAL",
            "PromotionId",
        ].astype(int)
    )

    targeted_ids = (
        bridge_product_ids
        | bridge_category_ids
        | bridge_store_ids
    )

    if seasonal_ids.intersection(
        targeted_ids
    ):
        raise ValueError(
            "Global seasonal promotion "
            "unexpectedly has a bridge."
        )