"""
UAE Retail Intelligence Platform
Synthetic Sales Generator

Generates:
- Sales Orders
- Sales Order Items
- Order Payments

Business behaviour includes:
- 2023-2025 growth
- UAE seasonal events
- Weekend effects
- Customer purchasing behaviour
- Customer channel preference
- Customer emirate preference
- Customer category preference
- Product popularity
- Product seasonality
- Promotions
- Financial calculations
- VAT
- COGS

This module DOES NOT write to SQL Server.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


# ============================================================
# Constants
# ============================================================

MONEY_QUANTIZER = Decimal("0.0001")


YEAR_WEIGHTS = {
    2023: 0.30,
    2024: 0.33,
    2025: 0.37,
}


PAYMENT_WEIGHTS = {
    "STORE": {
        "CASH": 0.18,
        "CREDIT_CARD": 0.42,
        "DEBIT_CARD": 0.28,
        "DIGITAL_WALLET": 0.12,
    },
    "ONLINE": {
        "CASH": 0.00,
        "CREDIT_CARD": 0.53,
        "DEBIT_CARD": 0.18,
        "DIGITAL_WALLET": 0.29,
    },
}


# ============================================================
# Financial Helpers
# ============================================================

def money(
    value: float | Decimal,
) -> Decimal:
    """
    Convert a value to project monetary precision.
    """

    return Decimal(
        str(value)
    ).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# Probability Helpers
# ============================================================

def _normalize(
    values: np.ndarray,
) -> np.ndarray:

    values = np.array(
        values,
        dtype=np.float64,
        copy=True,
    )

    if not np.isfinite(
        values
    ).all():
        raise ValueError(
            "Probability weights contain "
            "NaN or infinite values."
        )

    if (
        values < 0
    ).any():
        raise ValueError(
            "Probability weights cannot "
            "be negative."
        )

    total = float(
        values.sum()
    )

    if total <= 0:
        raise ValueError(
            "Probability weights sum "
            "to zero."
        )

    return (
        values
        / total
    )


# ============================================================
# Date Probabilities
# ============================================================

def _build_date_probabilities(
    dates: pd.DataFrame,
) -> np.ndarray:

    weights = np.ones(
        len(dates),
        dtype=np.float64,
    )

    years = np.array(
        dates[
            "YearNumber"
        ],
        dtype=np.int32,
        copy=True,
    )

    for (
        year,
        year_weight,
    ) in YEAR_WEIGHTS.items():

        mask = (
            years == year
        )

        year_days = int(
            mask.sum()
        )

        if year_days == 0:
            raise ValueError(
                f"No dates found for "
                f"{year}."
            )

        weights[mask] *= (
            year_weight
            / year_days
        )

    is_weekend = np.array(
        dates[
            "IsWeekend"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_weekend == 1,
        1.16,
        1.0,
    )

    is_ramadan = np.array(
        dates[
            "IsRamadan"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_ramadan == 1,
        1.17,
        1.0,
    )

    is_eid_fitr = np.array(
        dates[
            "IsEidAlFitr"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_eid_fitr == 1,
        1.42,
        1.0,
    )

    is_eid_adha = np.array(
        dates[
            "IsEidAlAdha"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_eid_adha == 1,
        1.34,
        1.0,
    )

    is_white_friday = np.array(
        dates[
            "IsWhiteFriday"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_white_friday == 1,
        1.85,
        1.0,
    )

    is_etihad = np.array(
        dates[
            "IsEidAlEtihad"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_etihad == 1,
        1.24,
        1.0,
    )

    is_year_end = np.array(
        dates[
            "IsYearEndSeason"
        ],
        dtype=np.int8,
        copy=True,
    )

    weights *= np.where(
        is_year_end == 1,
        1.30,
        1.0,
    )

    return _normalize(
        weights
    )


# ============================================================
# Store Probabilities
# ============================================================

def _build_store_probabilities(
    stores: pd.DataFrame,
) -> np.ndarray:

    floor_area = np.array(
        stores[
            "FloorAreaSqM"
        ],
        dtype=np.float64,
        copy=True,
    )

    if (
        floor_area <= 0
    ).any():
        raise ValueError(
            "Store floor area must "
            "be positive."
        )

    weights = np.sqrt(
        floor_area
    )

    return _normalize(
        weights
    )


# ============================================================
# Customer Probabilities
# ============================================================

def _build_customer_probabilities(
    customer_data: pd.DataFrame,
) -> np.ndarray:
    """
    Build writable probability array.

    copy=True intentionally avoids read-only
    arrays returned by some Pandas versions.
    """

    weights = np.array(
        customer_data[
            "PurchasePropensity"
        ],
        dtype=np.float64,
        copy=True,
    )

    active_flags = np.array(
        customer_data[
            "IsActive"
        ],
        dtype=np.int8,
        copy=True,
    )

    active_multiplier = np.where(
        active_flags == 1,
        1.0,
        0.15,
    )

    weights = (
        weights
        * active_multiplier
    )

    return _normalize(
        weights
    )


# ============================================================
# Promotion Lookups
# ============================================================

def _build_promotion_maps(
    promotions: pd.DataFrame,
    promotion_products: pd.DataFrame,
    promotion_categories: pd.DataFrame,
    promotion_stores: pd.DataFrame,
):

    promotion_records = {}

    for row in (
        promotions.itertuples(
            index=False
        )
    ):

        promotion_records[
            int(row.PromotionId)
        ] = {
            "PromotionId": int(
                row.PromotionId
            ),
            "PromotionType": str(
                row.PromotionType
            ),
            "DiscountType": str(
                row.DiscountType
            ),
            "DiscountValue": float(
                row.DiscountValue
            ),
            "StartDate": (
                pd.to_datetime(
                    row.StartDate
                ).date()
            ),
            "EndDate": (
                pd.to_datetime(
                    row.EndDate
                ).date()
            ),
        }

    product_map = {}

    for row in (
        promotion_products.itertuples(
            index=False
        )
    ):

        product_id = int(
            row.ProductId
        )

        promotion_id = int(
            row.PromotionId
        )

        product_map.setdefault(
            product_id,
            set(),
        ).add(
            promotion_id
        )

    category_map = {}

    for row in (
        promotion_categories.itertuples(
            index=False
        )
    ):

        category_id = int(
            row.CategoryId
        )

        promotion_id = int(
            row.PromotionId
        )

        category_map.setdefault(
            category_id,
            set(),
        ).add(
            promotion_id
        )

    store_map = {}

    for row in (
        promotion_stores.itertuples(
            index=False
        )
    ):

        store_id = int(
            row.StoreId
        )

        promotion_id = int(
            row.PromotionId
        )

        store_map.setdefault(
            store_id,
            set(),
        ).add(
            promotion_id
        )

    seasonal_ids = {
        int(row.PromotionId)
        for row
        in promotions.itertuples(
            index=False
        )
        if str(
            row.PromotionType
        )
        == "SEASONAL"
    }

    return (
        promotion_records,
        product_map,
        category_map,
        store_map,
        seasonal_ids,
    )


def _find_best_promotion(
    order_date,
    store_id: int,
    product_id: int,
    category_id: int,
    promotion_records,
    product_map,
    category_map,
    store_map,
    seasonal_ids,
):

    candidates = set(
        seasonal_ids
    )

    candidates.update(
        product_map.get(
            product_id,
            set(),
        )
    )

    candidates.update(
        category_map.get(
            category_id,
            set(),
        )
    )

    candidates.update(
        store_map.get(
            store_id,
            set(),
        )
    )

    applicable = []

    for promotion_id in (
        candidates
    ):

        promotion = (
            promotion_records[
                promotion_id
            ]
        )

        if not (
            promotion[
                "StartDate"
            ]
            <= order_date
            <= promotion[
                "EndDate"
            ]
        ):
            continue

        promotion_type = (
            promotion[
                "PromotionType"
            ]
        )

        if (
            promotion_type
            == "PRODUCT"
            and promotion_id
            not in product_map.get(
                product_id,
                set(),
            )
        ):
            continue

        if (
            promotion_type
            == "CATEGORY"
            and promotion_id
            not in category_map.get(
                category_id,
                set(),
            )
        ):
            continue

        if (
            promotion_type
            == "STORE"
            and promotion_id
            not in store_map.get(
                store_id,
                set(),
            )
        ):
            continue

        applicable.append(
            promotion
        )

    if not applicable:
        return None

    return max(
        applicable,
        key=lambda item: (
            item[
                "DiscountValue"
            ]
        ),
    )


# ============================================================
# Product Seasonality
# ============================================================

def _seasonality_multiplier(
    profile: str,
    date_row,
) -> float:

    if profile == "STABLE":
        return 1.0

    if (
        profile == "RAMADAN"
        and int(
            date_row.IsRamadan
        )
        == 1
    ):
        return 1.65

    if (
        profile == "EID"
        and (
            int(
                date_row.IsEidAlFitr
            )
            == 1
            or int(
                date_row.IsEidAlAdha
            )
            == 1
        )
    ):
        return 1.75

    if (
        profile == "SUMMER"
        and int(
            date_row.IsSummer
        )
        == 1
    ):
        return 1.55

    if (
        profile
        == "WHITE_FRIDAY"
        and int(
            date_row.IsWhiteFriday
        )
        == 1
    ):
        return 2.10

    if (
        profile == "YEAR_END"
        and int(
            date_row.IsYearEndSeason
        )
        == 1
    ):
        return 1.70

    return 0.92


# ============================================================
# Channel Selection
# ============================================================

def _choose_channel(
    rng: np.random.Generator,
    preferred_channel_id: int,
    channel_ids: np.ndarray,
) -> int:

    if rng.random() < 0.72:
        return int(
            preferred_channel_id
        )

    alternatives = (
        channel_ids[
            channel_ids
            != preferred_channel_id
        ]
    )

    if len(
        alternatives
    ) == 0:
        return int(
            preferred_channel_id
        )

    return int(
        rng.choice(
            alternatives
        )
    )


# ============================================================
# Store Selection
# ============================================================

def _choose_store(
    rng: np.random.Generator,
    store_ids: np.ndarray,
    base_probabilities: np.ndarray,
    preferred_emirate_id: int,
    store_to_emirate: dict[int, int],
) -> int:

    preference_multiplier = (
        np.array(
            [
                2.40
                if store_to_emirate[
                    int(store_id)
                ]
                == preferred_emirate_id
                else 1.0

                for store_id
                in store_ids
            ],
            dtype=np.float64,
        )
    )

    weights = (
        np.array(
            base_probabilities,
            dtype=np.float64,
            copy=True,
        )
        * preference_multiplier
    )

    weights = _normalize(
        weights
    )

    return int(
        rng.choice(
            store_ids,
            p=weights,
        )
    )


# ============================================================
# Product Selection
# ============================================================

def _choose_product(
    rng: np.random.Generator,
    eligible_products: pd.DataFrame,
    preferred_category_id: int,
    date_row,
):

    popularity = np.array(
        eligible_products[
            "PopularityScore"
        ],
        dtype=np.float64,
        copy=True,
    )

    weights = (
        popularity
        + 0.04
    )

    category_ids = np.array(
        eligible_products[
            "CategoryId"
        ],
        dtype=np.int32,
        copy=True,
    )

    category_multiplier = (
        np.where(
            category_ids
            == preferred_category_id,
            2.0,
            1.0,
        )
    )

    weights = (
        weights
        * category_multiplier
    )

    seasonal_multiplier = (
        np.array(
            [
                _seasonality_multiplier(
                    str(profile),
                    date_row,
                )

                for profile
                in eligible_products[
                    "SeasonalityProfile"
                ]
            ],
            dtype=np.float64,
        )
    )

    weights = (
        weights
        * seasonal_multiplier
    )

    weights = _normalize(
        weights
    )

    position = int(
        rng.choice(
            np.arange(
                len(
                    eligible_products
                )
            ),
            p=weights,
        )
    )

    return (
        eligible_products.iloc[
            position
        ]
    )


# ============================================================
# Payment Selection
# ============================================================

def _choose_payment_method(
    rng: np.random.Generator,
    channel_code: str,
    payment_methods: pd.DataFrame,
) -> int:

    if (
        channel_code
        not in PAYMENT_WEIGHTS
    ):
        raise ValueError(
            "Unsupported channel code: "
            f"{channel_code}"
        )

    weight_map = (
        PAYMENT_WEIGHTS[
            channel_code
        ]
    )

    codes = (
        payment_methods[
            "PaymentMethodCode"
        ]
        .astype(str)
        .tolist()
    )

    weights = np.array(
        [
            weight_map[
                code
            ]
            for code
            in codes
        ],
        dtype=np.float64,
    )

    weights = _normalize(
        weights
    )

    chosen_code = str(
        rng.choice(
            codes,
            p=weights,
        )
    )

    payment_method_id = int(
        payment_methods.loc[
            payment_methods[
                "PaymentMethodCode"
            ]
            == chosen_code,
            "PaymentMethodId",
        ].iloc[0]
    )

    return payment_method_id


# ============================================================
# Main Generator
# ============================================================

def generate_sales_datasets(
    dates: pd.DataFrame,
    stores: pd.DataFrame,
    cities: pd.DataFrame,
    customers: pd.DataFrame,
    customer_profiles: pd.DataFrame,
    sales_channels: pd.DataFrame,
    payment_methods: pd.DataFrame,
    products: pd.DataFrame,
    subcategories: pd.DataFrame,
    promotions: pd.DataFrame,
    promotion_products: pd.DataFrame,
    promotion_categories: pd.DataFrame,
    promotion_stores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:

    rng = np.random.default_rng(
        CONFIG.random_seed + 700
    )

    # ========================================================
    # Prepare Dates
    # ========================================================

    dates = (
        dates
        .copy()
        .sort_values(
            "DateKey"
        )
        .reset_index(
            drop=True
        )
    )

    dates[
        "FullDate"
    ] = pd.to_datetime(
        dates[
            "FullDate"
        ]
    ).dt.date

    # ========================================================
    # Prepare Customers
    # ========================================================

    customers = (
        customers
        .copy()
    )

    customers[
        "RegistrationDate"
    ] = pd.to_datetime(
        customers[
            "RegistrationDate"
        ]
    ).dt.date

    customer_profiles = (
        customer_profiles
        .copy()
    )

    customer_data = (
        customers.merge(
            customer_profiles,
            on="CustomerId",
            how="inner",
            validate="one_to_one",
        )
        .sort_values(
            "CustomerId"
        )
        .reset_index(
            drop=True
        )
    )

    if (
        len(customer_data)
        != len(customers)
    ):
        raise ValueError(
            "Customer/profile merge "
            "is incomplete."
        )

    # ========================================================
    # Prepare Products
    # ========================================================

    products = (
        products.copy()
    )

    products[
        "LaunchDate"
    ] = pd.to_datetime(
        products[
            "LaunchDate"
        ]
    ).dt.date

    products[
        "DiscontinuedDate"
    ] = pd.to_datetime(
        products[
            "DiscontinuedDate"
        ],
        errors="coerce",
    ).dt.date

    products = products.merge(
        subcategories[
            [
                "SubcategoryId",
                "CategoryId",
            ]
        ],
        on="SubcategoryId",
        how="left",
        validate="many_to_one",
    )

    if products[
        "CategoryId"
    ].isna().any():
        raise ValueError(
            "Unable to resolve "
            "Product.CategoryId."
        )

    # ========================================================
    # Build Probability Arrays
    # ========================================================

    date_probabilities = (
        _build_date_probabilities(
            dates
        )
    )

    customer_probabilities = (
        _build_customer_probabilities(
            customer_data
        )
    )

    store_probabilities = (
        _build_store_probabilities(
            stores
        )
    )

    # ========================================================
    # Geographic Lookups
    # ========================================================

    city_to_emirate = dict(
        zip(
            cities[
                "CityId"
            ].astype(int),

            cities[
                "EmirateId"
            ].astype(int),
        )
    )

    store_to_emirate = {}

    for row in (
        stores.itertuples(
            index=False
        )
    ):

        city_id = int(
            row.CityId
        )

        if (
            city_id
            not in city_to_emirate
        ):
            raise ValueError(
                "Invalid Store.CityId."
            )

        store_to_emirate[
            int(row.StoreId)
        ] = (
            city_to_emirate[
                city_id
            ]
        )

    store_ids = np.array(
        stores[
            "StoreId"
        ],
        dtype=np.int32,
        copy=True,
    )

    # ========================================================
    # Channel Lookups
    # ========================================================

    channel_lookup = dict(
        zip(
            sales_channels[
                "SalesChannelId"
            ].astype(int),

            sales_channels[
                "ChannelCode"
            ].astype(str),
        )
    )

    channel_ids = np.array(
        sales_channels[
            "SalesChannelId"
        ],
        dtype=np.int32,
        copy=True,
    )

    # ========================================================
    # Promotion Lookups
    # ========================================================

    (
        promotion_records,
        product_promotion_map,
        category_promotion_map,
        store_promotion_map,
        seasonal_promotion_ids,
    ) = _build_promotion_maps(
        promotions=promotions,
        promotion_products=(
            promotion_products
        ),
        promotion_categories=(
            promotion_categories
        ),
        promotion_stores=(
            promotion_stores
        ),
    )

    # ========================================================
    # Sample Dates
    # ========================================================

    number_of_orders = (
        CONFIG.target_number_of_orders
    )

    sampled_positions = (
        rng.choice(
            np.arange(
                len(dates)
            ),
            size=number_of_orders,
            replace=True,
            p=date_probabilities,
        )
    )

    selected_dates = (
        dates.iloc[
            sampled_positions
        ]
        .copy()
        .sort_values(
            [
                "FullDate",
                "DateKey",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Output Containers
    # ========================================================

    order_rows = []
    item_rows = []
    payment_rows = []

    next_order_item_id = 1
    next_payment_id = 1

    # ========================================================
    # Order Generation
    # ========================================================

    for (
        order_id,
        date_row,
    ) in enumerate(
        selected_dates.itertuples(
            index=False
        ),
        start=1,
    ):

        order_date = (
            date_row.FullDate
        )

        # ----------------------------------------------------
        # Eligible Customers
        # ----------------------------------------------------

        registration_dates = np.array(
            customer_data[
                "RegistrationDate"
            ],
            dtype=object,
            copy=True,
        )

        eligible_mask = (
            registration_dates
            <= order_date
        )

        eligible_indices = (
            np.flatnonzero(
                eligible_mask
            )
        )

        if (
            len(
                eligible_indices
            )
            == 0
        ):
            raise ValueError(
                "No eligible customers "
                f"for {order_date}."
            )

        eligible_weights = (
            customer_probabilities[
                eligible_indices
            ].copy()
        )

        eligible_weights = (
            _normalize(
                eligible_weights
            )
        )

        customer_position = int(
            rng.choice(
                eligible_indices,
                p=eligible_weights,
            )
        )

        customer = (
            customer_data.iloc[
                customer_position
            ]
        )

        customer_id = int(
            customer[
                "CustomerId"
            ]
        )

        # ----------------------------------------------------
        # Channel
        # ----------------------------------------------------

        preferred_channel_id = int(
            customer[
                "PreferredChannelId"
            ]
        )

        sales_channel_id = (
            _choose_channel(
                rng=rng,
                preferred_channel_id=(
                    preferred_channel_id
                ),
                channel_ids=(
                    channel_ids
                ),
            )
        )

        channel_code = (
            channel_lookup[
                sales_channel_id
            ]
        )

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

        store_id = (
            _choose_store(
                rng=rng,
                store_ids=store_ids,
                base_probabilities=(
                    store_probabilities
                ),
                preferred_emirate_id=int(
                    customer[
                        "PreferredEmirateId"
                    ]
                ),
                store_to_emirate=(
                    store_to_emirate
                ),
            )
        )

        # ----------------------------------------------------
        # Basket Size
        # ----------------------------------------------------

        expected_basket_size = float(
            customer[
                "ExpectedBasketSize"
            ]
        )

        basket_lambda = max(
            expected_basket_size
            - 1.0,
            0.10,
        )

        number_of_lines = int(
            1
            + rng.poisson(
                basket_lambda
            )
        )

        number_of_lines = int(
            np.clip(
                number_of_lines,
                CONFIG.minimum_items_per_order,
                CONFIG.maximum_items_per_order,
            )
        )

        # ----------------------------------------------------
        # Eligible Products
        # ----------------------------------------------------

        product_launch_dates = (
            products[
                "LaunchDate"
            ]
        )

        product_discontinued_dates = (
            products[
                "DiscontinuedDate"
            ]
        )

        eligible_products = (
            products.loc[
                (
                    product_launch_dates
                    <= order_date
                )
                & (
                    product_discontinued_dates
                    .isna()
                    | (
                        product_discontinued_dates
                        >= order_date
                    )
                )
            ]
            .copy()
            .reset_index(
                drop=True
            )
        )

        if eligible_products.empty:
            raise ValueError(
                "No eligible products "
                f"for {order_date}."
            )

        preferred_category_id = int(
            customer[
                "PreferredCategoryId"
            ]
        )

        chosen_product_ids = set()

        current_order_lines = []

        # ----------------------------------------------------
        # Order Items
        # ----------------------------------------------------

        for _ in range(
            number_of_lines
        ):

            available_products = (
                eligible_products.loc[
                    ~eligible_products[
                        "ProductId"
                    ]
                    .astype(int)
                    .isin(
                        chosen_product_ids
                    )
                ]
                .reset_index(
                    drop=True
                )
            )

            if (
                available_products.empty
            ):
                break

            product = (
                _choose_product(
                    rng=rng,
                    eligible_products=(
                        available_products
                    ),
                    preferred_category_id=(
                        preferred_category_id
                    ),
                    date_row=(
                        date_row
                    ),
                )
            )

            product_id = int(
                product[
                    "ProductId"
                ]
            )

            category_id = int(
                product[
                    "CategoryId"
                ]
            )

            chosen_product_ids.add(
                product_id
            )

            quantity = int(
                rng.choice(
                    [
                        1,
                        2,
                        3,
                        4,
                    ],
                    p=[
                        0.72,
                        0.20,
                        0.06,
                        0.02,
                    ],
                )
            )

            # ------------------------------------------------
            # Financial Snapshot
            # ------------------------------------------------

            unit_price = money(
                product[
                    "BaseSellingPrice"
                ]
            )

            unit_cost = money(
                product[
                    "StandardCost"
                ]
            )

            gross_amount = money(
                unit_price
                * quantity
            )

            # ------------------------------------------------
            # Promotion
            # ------------------------------------------------

            promotion = (
                _find_best_promotion(
                    order_date=(
                        order_date
                    ),
                    store_id=(
                        store_id
                    ),
                    product_id=(
                        product_id
                    ),
                    category_id=(
                        category_id
                    ),
                    promotion_records=(
                        promotion_records
                    ),
                    product_map=(
                        product_promotion_map
                    ),
                    category_map=(
                        category_promotion_map
                    ),
                    store_map=(
                        store_promotion_map
                    ),
                    seasonal_ids=(
                        seasonal_promotion_ids
                    ),
                )
            )

            promotion_id = None

            discount_amount = (
                money(0)
            )

            if (
                promotion
                is not None
            ):

                promotion_probability = (
                    0.45
                    + (
                        0.50
                        * float(
                            customer[
                                "PromotionSensitivity"
                            ]
                        )
                    )
                )

                promotion_probability = min(
                    promotion_probability,
                    0.98,
                )

                if (
                    rng.random()
                    < promotion_probability
                ):

                    promotion_id = int(
                        promotion[
                            "PromotionId"
                        ]
                    )

                    if (
                        promotion[
                            "DiscountType"
                        ]
                        == "PERCENTAGE"
                    ):

                        discount_rate = (
                            Decimal(
                                str(
                                    promotion[
                                        "DiscountValue"
                                    ]
                                )
                            )
                            / Decimal(
                                "100"
                            )
                        )

                        discount_amount = money(
                            gross_amount
                            * discount_rate
                        )

                    else:

                        fixed_discount = (
                            Decimal(
                                str(
                                    promotion[
                                        "DiscountValue"
                                    ]
                                )
                            )
                        )

                        discount_amount = money(
                            min(
                                gross_amount,
                                fixed_discount,
                            )
                        )

            if (
                discount_amount
                > gross_amount
            ):
                discount_amount = (
                    gross_amount
                )

            net_amount = money(
                gross_amount
                - discount_amount
            )

            vat_rate = Decimal(
                str(
                    product[
                        "DefaultVATRate"
                    ]
                )
            )

            vat_amount = money(
                net_amount
                * vat_rate
            )

            customer_total = money(
                net_amount
                + vat_amount
            )

            line_cogs = money(
                unit_cost
                * quantity
            )

            line = {
                "OrderItemId": (
                    next_order_item_id
                ),
                "OrderId": (
                    order_id
                ),
                "ProductId": (
                    product_id
                ),
                "PromotionId": (
                    promotion_id
                ),
                "Quantity": (
                    quantity
                ),
                "UnitPrice": (
                    unit_price
                ),
                "UnitCost": (
                    unit_cost
                ),
                "GrossAmount": (
                    gross_amount
                ),
                "DiscountAmount": (
                    discount_amount
                ),
                "NetAmount": (
                    net_amount
                ),
                "VATRate": (
                    vat_rate
                ),
                "VATAmount": (
                    vat_amount
                ),
                "CustomerTotal": (
                    customer_total
                ),
                "LineCOGS": (
                    line_cogs
                ),
            }

            current_order_lines.append(
                line
            )

            item_rows.append(
                line
            )

            next_order_item_id += 1

        if not current_order_lines:
            raise ValueError(
                "Order generated with "
                "no order items."
            )

        # ----------------------------------------------------
        # Order Timestamp
        # ----------------------------------------------------

        business_hours = np.arange(
            8,
            23,
        )

        hour_weights = np.array(
            [
                0.01,
                0.02,
                0.04,
                0.06,
                0.08,
                0.08,
                0.07,
                0.07,
                0.08,
                0.10,
                0.11,
                0.11,
                0.09,
                0.05,
                0.03,
            ],
            dtype=np.float64,
        )

        hour_weights = _normalize(
            hour_weights
        )

        hour = int(
            rng.choice(
                business_hours,
                p=hour_weights,
            )
        )

        minute = int(
            rng.integers(
                0,
                60,
            )
        )

        second = int(
            rng.integers(
                0,
                60,
            )
        )

        order_datetime = (
            pd.Timestamp(
                order_date
            )
            + pd.Timedelta(
                hours=hour,
                minutes=minute,
                seconds=second,
            )
        )

        # ----------------------------------------------------
        # Header Totals
        # ----------------------------------------------------

        gross_total = money(
            sum(
                (
                    line[
                        "GrossAmount"
                    ]
                    for line
                    in current_order_lines
                ),
                Decimal("0"),
            )
        )

        discount_total = money(
            sum(
                (
                    line[
                        "DiscountAmount"
                    ]
                    for line
                    in current_order_lines
                ),
                Decimal("0"),
            )
        )

        net_total = money(
            sum(
                (
                    line[
                        "NetAmount"
                    ]
                    for line
                    in current_order_lines
                ),
                Decimal("0"),
            )
        )

        vat_total = money(
            sum(
                (
                    line[
                        "VATAmount"
                    ]
                    for line
                    in current_order_lines
                ),
                Decimal("0"),
            )
        )

        customer_total = money(
            sum(
                (
                    line[
                        "CustomerTotal"
                    ]
                    for line
                    in current_order_lines
                ),
                Decimal("0"),
            )
        )

        order_rows.append(
            {
                "OrderId": (
                    order_id
                ),
                "OrderNumber": (
                    f"ORD"
                    f"{order_id:09d}"
                ),
                "CustomerId": (
                    customer_id
                ),
                "StoreId": (
                    store_id
                ),
                "SalesChannelId": (
                    sales_channel_id
                ),
                "DateKey": int(
                    date_row.DateKey
                ),
                "OrderDateTime": (
                    order_datetime
                ),
                "OrderStatus": (
                    "COMPLETED"
                ),
                "GrossAmount": (
                    gross_total
                ),
                "DiscountAmount": (
                    discount_total
                ),
                "NetAmount": (
                    net_total
                ),
                "VATAmount": (
                    vat_total
                ),
                "CustomerTotal": (
                    customer_total
                ),
            }
        )

        # ----------------------------------------------------
        # Payment
        # ----------------------------------------------------

        payment_method_id = (
            _choose_payment_method(
                rng=rng,
                channel_code=(
                    channel_code
                ),
                payment_methods=(
                    payment_methods
                ),
            )
        )

        payment_rows.append(
            {
                "OrderPaymentId": (
                    next_payment_id
                ),
                "OrderId": (
                    order_id
                ),
                "PaymentMethodId": (
                    payment_method_id
                ),
                "PaymentAmount": (
                    customer_total
                ),
                "PaymentDateTime": (
                    order_datetime
                ),
                "PaymentReference": (
                    f"PAY"
                    f"{next_payment_id:010d}"
                ),
            }
        )

        next_payment_id += 1

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            order_id % 10_000
            == 0
        ):
            print(
                f"Generated "
                f"{order_id:,} / "
                f"{number_of_orders:,} "
                f"orders..."
            )

    # ========================================================
    # DataFrames
    # ========================================================

    orders = pd.DataFrame(
        order_rows
    )

    order_items = pd.DataFrame(
        item_rows
    )

    order_payments = pd.DataFrame(
        payment_rows
    )

    datasets = {
        "orders": (
            orders
        ),
        "order_items": (
            order_items
        ),
        "order_payments": (
            order_payments
        ),
    }

    validate_sales_data(
        datasets=datasets,
        customers=customers,
        stores=stores,
        sales_channels=(
            sales_channels
        ),
        payment_methods=(
            payment_methods
        ),
        products=products,
    )

    return datasets


# ============================================================
# Validation
# ============================================================

def validate_sales_data(
    datasets: dict[str, pd.DataFrame],
    customers: pd.DataFrame,
    stores: pd.DataFrame,
    sales_channels: pd.DataFrame,
    payment_methods: pd.DataFrame,
    products: pd.DataFrame,
) -> None:

    orders = (
        datasets[
            "orders"
        ]
    )

    items = (
        datasets[
            "order_items"
        ]
    )

    payments = (
        datasets[
            "order_payments"
        ]
    )

    # --------------------------------------------------------
    # Row Counts
    # --------------------------------------------------------

    if (
        len(orders)
        != CONFIG.target_number_of_orders
    ):
        raise ValueError(
            "Incorrect order count."
        )

    if (
        len(payments)
        != len(orders)
    ):
        raise ValueError(
            "Expected one payment "
            "per order."
        )

    if items.empty:
        raise ValueError(
            "No sales order items."
        )

    # --------------------------------------------------------
    # Unique Keys
    # --------------------------------------------------------

    unique_checks = [
        (
            orders,
            "OrderId",
        ),
        (
            orders,
            "OrderNumber",
        ),
        (
            items,
            "OrderItemId",
        ),
        (
            payments,
            "OrderPaymentId",
        ),
        (
            payments,
            "PaymentReference",
        ),
    ]

    for (
        dataframe,
        column,
    ) in unique_checks:

        if not dataframe[
            column
        ].is_unique:

            raise ValueError(
                f"Duplicate "
                f"{column}."
            )

    # --------------------------------------------------------
    # Foreign Keys
    # --------------------------------------------------------

    if not orders[
        "CustomerId"
    ].isin(
        customers[
            "CustomerId"
        ]
    ).all():

        raise ValueError(
            "Invalid order CustomerId."
        )

    if not orders[
        "StoreId"
    ].isin(
        stores[
            "StoreId"
        ]
    ).all():

        raise ValueError(
            "Invalid order StoreId."
        )

    if not orders[
        "SalesChannelId"
    ].isin(
        sales_channels[
            "SalesChannelId"
        ]
    ).all():

        raise ValueError(
            "Invalid SalesChannelId."
        )

    if not items[
        "OrderId"
    ].isin(
        orders[
            "OrderId"
        ]
    ).all():

        raise ValueError(
            "Orphan SalesOrderItem."
        )

    if not items[
        "ProductId"
    ].isin(
        products[
            "ProductId"
        ]
    ).all():

        raise ValueError(
            "Invalid ProductId."
        )

    if not payments[
        "OrderId"
    ].isin(
        orders[
            "OrderId"
        ]
    ).all():

        raise ValueError(
            "Orphan OrderPayment."
        )

    if not payments[
        "PaymentMethodId"
    ].isin(
        payment_methods[
            "PaymentMethodId"
        ]
    ).all():

        raise ValueError(
            "Invalid PaymentMethodId."
        )

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    if (
        items[
            "Quantity"
        ]
        <= 0
    ).any():

        raise ValueError(
            "Invalid sales quantity."
        )

    # --------------------------------------------------------
    # Financial Validation
    # --------------------------------------------------------

    for row in (
        items.itertuples(
            index=False
        )
    ):

        quantity = int(
            row.Quantity
        )

        unit_price = money(
            row.UnitPrice
        )

        unit_cost = money(
            row.UnitCost
        )

        gross = money(
            row.GrossAmount
        )

        discount = money(
            row.DiscountAmount
        )

        net = money(
            row.NetAmount
        )

        vat_rate = Decimal(
            str(
                row.VATRate
            )
        )

        vat = money(
            row.VATAmount
        )

        total = money(
            row.CustomerTotal
        )

        cogs = money(
            row.LineCOGS
        )

        if gross != money(
            unit_price
            * quantity
        ):
            raise ValueError(
                "GrossAmount validation "
                f"failed for OrderItemId "
                f"{row.OrderItemId}."
            )

        if (
            discount < 0
            or discount > gross
        ):
            raise ValueError(
                "Invalid discount for "
                f"OrderItemId "
                f"{row.OrderItemId}."
            )

        if net != money(
            gross
            - discount
        ):
            raise ValueError(
                "NetAmount validation "
                f"failed for OrderItemId "
                f"{row.OrderItemId}."
            )

        if vat != money(
            net
            * vat_rate
        ):
            raise ValueError(
                "VAT validation failed "
                f"for OrderItemId "
                f"{row.OrderItemId}."
            )

        if total != money(
            net
            + vat
        ):
            raise ValueError(
                "CustomerTotal validation "
                f"failed for OrderItemId "
                f"{row.OrderItemId}."
            )

        if cogs != money(
            unit_cost
            * quantity
        ):
            raise ValueError(
                "COGS validation failed "
                f"for OrderItemId "
                f"{row.OrderItemId}."
            )

    # --------------------------------------------------------
    # Items Per Order
    # --------------------------------------------------------

    item_counts = (
        items.groupby(
            "OrderId"
        ).size()
    )

    if (
        item_counts
        < CONFIG.minimum_items_per_order
    ).any():

        raise ValueError(
            "Order below minimum "
            "item count."
        )

    if (
        item_counts
        > CONFIG.maximum_items_per_order
    ).any():

        raise ValueError(
            "Order exceeds maximum "
            "item count."
        )

    # --------------------------------------------------------
    # Header Reconciliation
    # --------------------------------------------------------

    monetary_columns = [
        "GrossAmount",
        "DiscountAmount",
        "NetAmount",
        "VATAmount",
        "CustomerTotal",
    ]

    item_totals = (
        items.groupby(
            "OrderId"
        )[
            monetary_columns
        ]
        .sum()
        .reset_index()
    )

    reconciliation = (
        orders[
            [
                "OrderId",
                *monetary_columns,
            ]
        ]
        .merge(
            item_totals,
            on="OrderId",
            how="inner",
            suffixes=(
                "_Header",
                "_Items",
            ),
            validate="one_to_one",
        )
    )

    if (
        len(reconciliation)
        != len(orders)
    ):
        raise ValueError(
            "Header/item reconciliation "
            "missing orders."
        )

    for column in (
        monetary_columns
    ):

        header_values = (
            reconciliation[
                f"{column}_Header"
            ]
            .map(money)
        )

        item_values = (
            reconciliation[
                f"{column}_Items"
            ]
            .map(money)
        )

        if not (
            header_values
            == item_values
        ).all():

            raise ValueError(
                "Header reconciliation "
                f"failed for {column}."
            )

    # --------------------------------------------------------
    # Payment Reconciliation
    # --------------------------------------------------------

    payment_totals = (
        payments.groupby(
            "OrderId"
        )[
            "PaymentAmount"
        ]
        .sum()
        .reset_index()
    )

    payment_check = (
        orders[
            [
                "OrderId",
                "CustomerTotal",
            ]
        ]
        .merge(
            payment_totals,
            on="OrderId",
            how="inner",
            validate="one_to_one",
        )
    )

    if (
        len(payment_check)
        != len(orders)
    ):
        raise ValueError(
            "Missing payment."
        )

    expected_totals = (
        payment_check[
            "CustomerTotal"
        ]
        .map(money)
    )

    actual_totals = (
        payment_check[
            "PaymentAmount"
        ]
        .map(money)
    )

    if not (
        expected_totals
        == actual_totals
    ).all():

        raise ValueError(
            "Payment reconciliation "
            "failed."
        )

    # --------------------------------------------------------
    # Date Range
    # --------------------------------------------------------

    order_dates = (
        pd.to_datetime(
            orders[
                "OrderDateTime"
            ]
        ).dt.date
    )

    if (
        order_dates.min()
        < CONFIG.start_date
    ):
        raise ValueError(
            "Order before simulation "
            "period."
        )

    if (
        order_dates.max()
        > CONFIG.end_date
    ):
        raise ValueError(
            "Order after simulation "
            "period."
        )

    # --------------------------------------------------------
    # Registration Date
    # --------------------------------------------------------

    customer_registration = (
        customers[
            [
                "CustomerId",
                "RegistrationDate",
            ]
        ].copy()
    )

    customer_registration[
        "RegistrationDate"
    ] = pd.to_datetime(
        customer_registration[
            "RegistrationDate"
        ]
    ).dt.date

    registration_check = (
        orders[
            [
                "OrderId",
                "CustomerId",
                "OrderDateTime",
            ]
        ]
        .merge(
            customer_registration,
            on="CustomerId",
            how="left",
            validate="many_to_one",
        )
    )

    registration_check[
        "OrderDate"
    ] = pd.to_datetime(
        registration_check[
            "OrderDateTime"
        ]
    ).dt.date

    invalid_registration = (
        registration_check[
            "OrderDate"
        ]
        < registration_check[
            "RegistrationDate"
        ]
    )

    if (
        invalid_registration.any()
    ):
        raise ValueError(
            "Customer purchase before "
            "registration detected."
        )

    print(
        "Sales validation completed "
        "successfully."
    )