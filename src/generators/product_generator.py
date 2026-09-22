"""
Synthetic product master-data generator.

Generates:
- Categories
- Subcategories
- Brands
- Suppliers
- Products
- ProductSupplier relationships

This module does not connect to SQL Server.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


# ============================================================
# Product taxonomy
# ============================================================

CATEGORY_CONFIG = {
    "Fashion": {
        "subcategories": [
            "Men Clothing",
            "Women Clothing",
            "Footwear",
            "Accessories",
        ],
        "price_range": (40, 900),
        "margin_range": (0.42, 0.65),
        "return_range": (0.08, 0.18),
        "seasonality": [
            "STABLE",
            "EID",
            "YEAR_END",
        ],
    },

    "Electronics": {
        "subcategories": [
            "Smartphones",
            "Computers",
            "Audio",
            "Accessories",
        ],
        "price_range": (50, 6000),
        "margin_range": (0.12, 0.30),
        "return_range": (0.03, 0.09),
        "seasonality": [
            "STABLE",
            "WHITE_FRIDAY",
            "YEAR_END",
        ],
    },

    "Beauty": {
        "subcategories": [
            "Skincare",
            "Makeup",
            "Fragrances",
            "Hair Care",
        ],
        "price_range": (25, 800),
        "margin_range": (0.45, 0.70),
        "return_range": (0.01, 0.05),
        "seasonality": [
            "STABLE",
            "RAMADAN",
            "EID",
        ],
    },

    "Home": {
        "subcategories": [
            "Kitchen",
            "Home Decor",
            "Bedding",
            "Small Appliances",
        ],
        "price_range": (30, 2500),
        "margin_range": (0.30, 0.55),
        "return_range": (0.02, 0.07),
        "seasonality": [
            "STABLE",
            "RAMADAN",
            "YEAR_END",
        ],
    },

    "Sports": {
        "subcategories": [
            "Fitness",
            "Running",
            "Outdoor",
            "Sportswear",
        ],
        "price_range": (30, 1500),
        "margin_range": (0.30, 0.55),
        "return_range": (0.03, 0.09),
        "seasonality": [
            "STABLE",
            "SUMMER",
            "YEAR_END",
        ],
    },

    "Grocery": {
        "subcategories": [
            "Snacks",
            "Beverages",
            "Coffee & Tea",
            "Premium Food",
        ],
        "price_range": (5, 250),
        "margin_range": (0.15, 0.35),
        "return_range": (0.002, 0.015),
        "seasonality": [
            "STABLE",
            "RAMADAN",
            "EID",
        ],
    },

    "Toys": {
        "subcategories": [
            "Educational Toys",
            "Action & Dolls",
            "Games",
            "Outdoor Toys",
        ],
        "price_range": (20, 1200),
        "margin_range": (0.30, 0.55),
        "return_range": (0.02, 0.06),
        "seasonality": [
            "STABLE",
            "EID",
            "YEAR_END",
        ],
    },

    "Lifestyle": {
        "subcategories": [
            "Travel",
            "Stationery",
            "Gifts",
            "Personal Accessories",
        ],
        "price_range": (10, 1000),
        "margin_range": (0.35, 0.60),
        "return_range": (0.02, 0.07),
        "seasonality": [
            "STABLE",
            "EID",
            "YEAR_END",
        ],
    },
}


CATEGORY_WEIGHTS = {
    "Fashion": 0.18,
    "Electronics": 0.15,
    "Beauty": 0.13,
    "Home": 0.13,
    "Sports": 0.11,
    "Grocery": 0.12,
    "Toys": 0.08,
    "Lifestyle": 0.10,
}


BRAND_PREFIXES = [
    "Nova",
    "Urban",
    "Prime",
    "Aura",
    "Vertex",
    "Elite",
    "Nexa",
    "Luma",
    "Royal",
    "Vista",
    "Pulse",
    "Zen",
    "Orbit",
    "Metro",
    "Core",
]


BRAND_SUFFIXES = [
    "One",
    "Plus",
    "Living",
    "Works",
]


SUPPLIER_LOCATIONS = [
    "Dubai",
    "Abu Dhabi",
    "Sharjah",
    "Ajman",
    "Ras Al Khaimah",
    "Fujairah",
]


# ============================================================
# Helpers
# ============================================================

def _money(value: float) -> float:
    return round(float(value), 4)


def _probability(value: float) -> float:
    return round(float(value), 6)


# ============================================================
# Categories
# ============================================================

def generate_categories() -> pd.DataFrame:
    rows = []

    for category_id, category_name in enumerate(
        CATEGORY_CONFIG.keys(),
        start=1,
    ):
        rows.append(
            {
                "CategoryId": category_id,
                "CategoryName": category_name,
                "IsActive": 1,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Subcategories
# ============================================================

def generate_subcategories(
    categories: pd.DataFrame,
) -> pd.DataFrame:
    category_lookup = dict(
        zip(
            categories["CategoryName"],
            categories["CategoryId"],
        )
    )

    rows = []
    subcategory_id = 1

    for category_name, config in (
        CATEGORY_CONFIG.items()
    ):
        category_id = category_lookup[category_name]

        for subcategory_name in config["subcategories"]:
            rows.append(
                {
                    "SubcategoryId": subcategory_id,
                    "CategoryId": category_id,
                    "SubcategoryName": subcategory_name,
                    "IsActive": 1,
                }
            )

            subcategory_id += 1

    return pd.DataFrame(rows)


# ============================================================
# Brands
# ============================================================

def generate_brands() -> pd.DataFrame:
    brand_names = []

    for prefix in BRAND_PREFIXES:
        for suffix in BRAND_SUFFIXES:
            brand_names.append(
                f"{prefix} {suffix}"
            )

    if len(brand_names) != CONFIG.number_of_brands:
        raise ValueError(
            "Brand configuration must generate "
            f"{CONFIG.number_of_brands} brands."
        )

    rows = []

    for brand_id, brand_name in enumerate(
        brand_names,
        start=1,
    ):
        rows.append(
            {
                "BrandId": brand_id,
                "BrandName": brand_name,
                "IsActive": 1,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Suppliers
# ============================================================

def generate_suppliers() -> pd.DataFrame:
    rng = np.random.default_rng(
        CONFIG.random_seed + 100
    )

    rows = []

    for supplier_id in range(
        1,
        CONFIG.number_of_suppliers + 1,
    ):
        location = rng.choice(
            SUPPLIER_LOCATIONS
        )

        rows.append(
            {
                "SupplierId": supplier_id,
                "SupplierCode": (
                    f"SUP{supplier_id:03d}"
                ),
                "SupplierName": (
                    f"Gulf Supply "
                    f"{supplier_id:02d} - {location}"
                ),
                "ContactEmail": (
                    f"supplier{supplier_id:02d}"
                    "@example.com"
                ),
                "ContactPhone": (
                    f"+971500{supplier_id:05d}"
                ),
                "IsActive": 1,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Products
# ============================================================

def generate_products(
    categories: pd.DataFrame,
    subcategories: pd.DataFrame,
    brands: pd.DataFrame,
) -> pd.DataFrame:
    rng = np.random.default_rng(
        CONFIG.random_seed + 200
    )

    category_lookup = dict(
        zip(
            categories["CategoryId"],
            categories["CategoryName"],
        )
    )

    category_names = list(
        CATEGORY_WEIGHTS.keys()
    )

    category_probabilities = [
        CATEGORY_WEIGHTS[name]
        for name in category_names
    ]

    category_name_to_id = dict(
        zip(
            categories["CategoryName"],
            categories["CategoryId"],
        )
    )

    rows = []

    for product_id in range(
        1,
        CONFIG.number_of_products + 1,
    ):
        category_name = str(
            rng.choice(
                category_names,
                p=category_probabilities,
            )
        )

        category_id = category_name_to_id[
            category_name
        ]

        eligible_subcategories = (
            subcategories.loc[
                subcategories["CategoryId"]
                == category_id
            ]
        )

        selected_subcategory = (
            eligible_subcategories.iloc[
                int(
                    rng.integers(
                        0,
                        len(eligible_subcategories),
                    )
                )
            ]
        )

        subcategory_id = int(
            selected_subcategory["SubcategoryId"]
        )

        subcategory_name = str(
            selected_subcategory[
                "SubcategoryName"
            ]
        )

        brand_id = int(
            rng.choice(
                brands["BrandId"].to_numpy()
            )
        )

        brand_name = str(
            brands.loc[
                brands["BrandId"] == brand_id,
                "BrandName",
            ].iloc[0]
        )

        config = CATEGORY_CONFIG[
            category_name
        ]

        min_price, max_price = (
            config["price_range"]
        )

        # Log-normal-like distribution gives many
        # normal-priced products and fewer expensive ones.
        normalized_price = (
            rng.beta(2.0, 5.0)
        )

        selling_price = (
            min_price
            + normalized_price
            * (max_price - min_price)
        )

        selling_price = max(
            selling_price,
            min_price,
        )

        margin_min, margin_max = (
            config["margin_range"]
        )

        margin_rate = rng.uniform(
            margin_min,
            margin_max,
        )

        standard_cost = (
            selling_price
            * (1 - margin_rate)
        )

        return_min, return_max = (
            config["return_range"]
        )

        return_probability = rng.uniform(
            return_min,
            return_max,
        )

        popularity_score = rng.beta(
            2.2,
            4.0,
        )

        # Small number of highly popular products.
        if rng.random() < 0.08:
            popularity_score = rng.uniform(
                0.75,
                1.0,
            )

        seasonality_options = (
            config["seasonality"]
        )

        # Stable products are intentionally common.
        seasonality_weights = [
            0.60
            if value == "STABLE"
            else (
                0.40
                / (
                    len(
                        seasonality_options
                    )
                    - 1
                )
                if len(
                    seasonality_options
                ) > 1
                else 0
            )
            for value in seasonality_options
        ]

        seasonality = str(
            rng.choice(
                seasonality_options,
                p=seasonality_weights,
            )
        )

        launch_start = pd.Timestamp(
            "2018-01-01"
        )

        launch_end = pd.Timestamp(
            "2024-06-30"
        )

        launch_span_days = (
            launch_end - launch_start
        ).days

        launch_date = (
            launch_start
            + timedelta(
                days=int(
                    rng.integers(
                        0,
                        launch_span_days + 1,
                    )
                )
            )
        ).date()

        discontinued_date = None
        is_active = 1

        # A small group is discontinued during 2024/2025.
        if (
            launch_date
            < pd.Timestamp(
                "2024-01-01"
            ).date()
            and rng.random() < 0.04
        ):
            discontinue_start = max(
                pd.Timestamp(
                    launch_date
                ),
                pd.Timestamp(
                    "2024-01-01"
                ),
            )

            discontinue_end = pd.Timestamp(
                "2025-12-31"
            )

            days = (
                discontinue_end
                - discontinue_start
            ).days

            discontinued_date = (
                discontinue_start
                + timedelta(
                    days=int(
                        rng.integers(
                            0,
                            days + 1,
                        )
                    )
                )
            ).date()

            is_active = 0

        rows.append(
            {
                "ProductId": product_id,
                "SubcategoryId": (
                    subcategory_id
                ),
                "BrandId": brand_id,
                "SKU": (
                    f"SKU{product_id:06d}"
                ),
                "ProductName": (
                    f"{brand_name} "
                    f"{subcategory_name} "
                    f"{product_id:04d}"
                ),
                "BaseSellingPrice": _money(
                    selling_price
                ),
                "StandardCost": _money(
                    standard_cost
                ),
                "DefaultVATRate": (
                    CONFIG.default_vat_rate
                ),
                "PopularityScore": (
                    _probability(
                        popularity_score
                    )
                ),
                "SeasonalityProfile": (
                    seasonality
                ),
                "BaseReturnProbability": (
                    _probability(
                        return_probability
                    )
                ),
                "LaunchDate": launch_date,
                "DiscontinuedDate": (
                    discontinued_date
                ),
                "IsActive": is_active,
            }
        )

    products = pd.DataFrame(rows)

    if len(category_lookup) != 8:
        raise ValueError(
            "Unexpected category configuration."
        )

    return products


# ============================================================
# Product Suppliers
# ============================================================

def generate_product_suppliers(
    products: pd.DataFrame,
    suppliers: pd.DataFrame,
) -> pd.DataFrame:
    rng = np.random.default_rng(
        CONFIG.random_seed + 300
    )

    supplier_ids = (
        suppliers["SupplierId"]
        .to_numpy()
    )

    rows = []

    for product in products.itertuples(
        index=False
    ):
        # Most products have 1 supplier.
        # Some have 2 or 3.
        supplier_count = int(
            rng.choice(
                [1, 2, 3],
                p=[0.70, 0.25, 0.05],
            )
        )

        selected_suppliers = rng.choice(
            supplier_ids,
            size=supplier_count,
            replace=False,
        )

        primary_supplier = int(
            selected_suppliers[0]
        )

        for supplier_id_raw in (
            selected_suppliers
        ):
            supplier_id = int(
                supplier_id_raw
            )

            supplier_cost_variation = (
                rng.uniform(
                    0.92,
                    1.08,
                )
            )

            supplier_cost = (
                float(product.StandardCost)
                * supplier_cost_variation
            )

            lead_time_days = int(
                rng.integers(
                    2,
                    31,
                )
            )

            rows.append(
                {
                    "ProductId": (
                        int(product.ProductId)
                    ),
                    "SupplierId": supplier_id,
                    "SupplierProductCode": (
                        f"S{supplier_id:03d}"
                        f"-P{int(product.ProductId):06d}"
                    ),
                    "SupplierCost": _money(
                        supplier_cost
                    ),
                    "LeadTimeDays": (
                        lead_time_days
                    ),
                    "IsPrimarySupplier": int(
                        supplier_id
                        == primary_supplier
                    ),
                    "IsActive": 1,
                }
            )

    return pd.DataFrame(rows)


# ============================================================
# Validation
# ============================================================

def validate_product_data(
    datasets: dict[str, pd.DataFrame],
) -> None:
    categories = datasets["categories"]
    subcategories = datasets[
        "subcategories"
    ]
    brands = datasets["brands"]
    suppliers = datasets["suppliers"]
    products = datasets["products"]
    product_suppliers = datasets[
        "product_suppliers"
    ]

    expected_counts = {
        "categories": (
            CONFIG.number_of_categories
        ),
        "subcategories": 32,
        "brands": (
            CONFIG.number_of_brands
        ),
        "suppliers": (
            CONFIG.number_of_suppliers
        ),
        "products": (
            CONFIG.number_of_products
        ),
    }

    actual_frames = {
        "categories": categories,
        "subcategories": subcategories,
        "brands": brands,
        "suppliers": suppliers,
        "products": products,
    }

    for name, expected in (
        expected_counts.items()
    ):
        actual = len(
            actual_frames[name]
        )

        if actual != expected:
            raise ValueError(
                f"{name}: expected "
                f"{expected}, got {actual}."
            )

    unique_checks = [
        (
            categories,
            "CategoryId",
            "CategoryId",
        ),
        (
            categories,
            "CategoryName",
            "CategoryName",
        ),
        (
            subcategories,
            "SubcategoryId",
            "SubcategoryId",
        ),
        (
            brands,
            "BrandId",
            "BrandId",
        ),
        (
            brands,
            "BrandName",
            "BrandName",
        ),
        (
            suppliers,
            "SupplierId",
            "SupplierId",
        ),
        (
            suppliers,
            "SupplierCode",
            "SupplierCode",
        ),
        (
            products,
            "ProductId",
            "ProductId",
        ),
        (
            products,
            "SKU",
            "SKU",
        ),
    ]

    for dataframe, column, label in (
        unique_checks
    ):
        if not dataframe[column].is_unique:
            raise ValueError(
                f"Duplicate {label} detected."
            )

    if not subcategories[
        "CategoryId"
    ].isin(
        categories["CategoryId"]
    ).all():
        raise ValueError(
            "Orphan Subcategory.CategoryId."
        )

    if not products[
        "SubcategoryId"
    ].isin(
        subcategories["SubcategoryId"]
    ).all():
        raise ValueError(
            "Orphan Product.SubcategoryId."
        )

    if not products[
        "BrandId"
    ].isin(
        brands["BrandId"]
    ).all():
        raise ValueError(
            "Orphan Product.BrandId."
        )

    if not product_suppliers[
        "ProductId"
    ].isin(
        products["ProductId"]
    ).all():
        raise ValueError(
            "Orphan ProductSupplier.ProductId."
        )

    if not product_suppliers[
        "SupplierId"
    ].isin(
        suppliers["SupplierId"]
    ).all():
        raise ValueError(
            "Orphan ProductSupplier.SupplierId."
        )

    if (
        products["BaseSellingPrice"]
        < 0
    ).any():
        raise ValueError(
            "Negative selling price."
        )

    if (
        products["StandardCost"]
        < 0
    ).any():
        raise ValueError(
            "Negative standard cost."
        )

    if (
        products["StandardCost"]
        > products["BaseSellingPrice"]
    ).any():
        raise ValueError(
            "StandardCost exceeds "
            "BaseSellingPrice."
        )

    if not products[
        "PopularityScore"
    ].between(
        0,
        1,
    ).all():
        raise ValueError(
            "Invalid PopularityScore."
        )

    if not products[
        "BaseReturnProbability"
    ].between(
        0,
        1,
    ).all():
        raise ValueError(
            "Invalid return probability."
        )

    duplicate_bridges = (
        product_suppliers
        .duplicated(
            subset=[
                "ProductId",
                "SupplierId",
            ]
        )
        .any()
    )

    if duplicate_bridges:
        raise ValueError(
            "Duplicate product-supplier pair."
        )

    primary_counts = (
        product_suppliers.loc[
            (
                product_suppliers[
                    "IsPrimarySupplier"
                ]
                == 1
            )
            & (
                product_suppliers[
                    "IsActive"
                ]
                == 1
            )
        ]
        .groupby("ProductId")
        .size()
    )

    if (
        len(primary_counts)
        != len(products)
    ):
        raise ValueError(
            "Not every product has "
            "a primary supplier."
        )

    if not (
        primary_counts == 1
    ).all():
        raise ValueError(
            "A product has multiple "
            "active primary suppliers."
        )


# ============================================================
# Main interface
# ============================================================

def generate_product_datasets(
) -> dict[str, pd.DataFrame]:
    categories = generate_categories()

    subcategories = (
        generate_subcategories(
            categories=categories
        )
    )

    brands = generate_brands()

    suppliers = generate_suppliers()

    products = generate_products(
        categories=categories,
        subcategories=subcategories,
        brands=brands,
    )

    product_suppliers = (
        generate_product_suppliers(
            products=products,
            suppliers=suppliers,
        )
    )

    datasets = {
        "categories": categories,
        "subcategories": subcategories,
        "brands": brands,
        "suppliers": suppliers,
        "products": products,
        "product_suppliers": (
            product_suppliers
        ),
    }

    validate_product_data(
        datasets
    )

    return datasets