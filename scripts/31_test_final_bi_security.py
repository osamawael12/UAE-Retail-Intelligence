"""
UAE Retail Intelligence Platform
STEP 31 - Final BI Security & Filter Verification

Final verification before closing the BI dashboard phase.

Validates:
- CEO full scope
- Dubai Manager RLS scope
- Store Manager RLS scope
- Date filtering
- Emirate filtering
- Store filtering
- Customer filtering
- Promotion filtering
- Returns filtering
- Inventory geography filtering
- Target filtering
- Cross-scope filter bypass resistance
- EXPORT_DATA permission model

This test does not modify business data.
"""

from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv

from app.filters import (
    DashboardFilters,
)
from src.analytics.customer_data import (
    get_filtered_customer_summary,
)
from src.analytics.filtered_data import (
    get_filtered_emirate_performance,
    get_filtered_inventory,
    get_filtered_product_performance,
    get_filtered_returns,
    get_filtered_store_performance,
    get_filtered_summary,
)
from src.analytics.promotion_data import (
    get_promotion_kpis,
)
from src.analytics.target_data import (
    get_filtered_store_targets,
    get_filtered_target_summary,
)
from src.security.authentication import (
    authenticate,
)


# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# Test Helpers
# ============================================================

def check(
    condition: bool,
    message: str,
) -> int:
    if condition:
        print(
            f"[PASS] {message}"
        )
        return 0

    print(
        f"[FAIL] {message}"
    )

    return 1


def load_user(
    username: str,
    password_environment_variable: str,
):
    password = os.getenv(
        password_environment_variable
    )

    if not password:
        raise RuntimeError(
            "Missing environment variable: "
            f"{password_environment_variable}"
        )

    user = authenticate(
        username=username,
        password=password,
    )

    if user is None:
        raise RuntimeError(
            "Authentication failed for "
            f"{username}"
        )

    return user


def make_filters(
    start_date=None,
    end_date=None,
    emirates=(),
    store_ids=(),
) -> DashboardFilters:
    return DashboardFilters(
        start_date=start_date,
        end_date=end_date,
        emirates=tuple(
            emirates
        ),
        store_ids=tuple(
            store_ids
        ),
    )


def almost_equal(
    left,
    right,
    tolerance: float = 0.02,
) -> bool:
    return (
        abs(
            float(left or 0)
            - float(right or 0)
        )
        <= tolerance
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    print(
        "=" * 78
    )

    print(
        "UAE Retail Intelligence Platform"
    )

    print(
        "STEP 31 - FINAL BI SECURITY "
        "& FILTER VERIFICATION"
    )

    print(
        "=" * 78
    )

    failures = 0

    # --------------------------------------------------------
    # Authenticate personas
    # --------------------------------------------------------

    ceo = load_user(
        "ceo",
        "DEMO_CEO_PASSWORD",
    )

    dubai = load_user(
        "dubai.manager",
        "DEMO_DUBAI_MANAGER_PASSWORD",
    )

    store_manager = load_user(
        "store.manager",
        "DEMO_STORE_MANAGER_PASSWORD",
    )

    inventory_analyst = load_user(
        "inventory.analyst",
        "DEMO_INVENTORY_PASSWORD",
    )

    print(
        "\n[1] AUTHENTICATED PERSONAS"
    )

    failures += check(
        ceo.username == "ceo",
        "CEO authenticated",
    )

    failures += check(
        dubai.username
        == "dubai.manager",
        "Dubai Manager authenticated",
    )

    failures += check(
        store_manager.username
        == "store.manager",
        "Store Manager authenticated",
    )

    failures += check(
        inventory_analyst.username
        == "inventory.analyst",
        "Inventory Analyst authenticated",
    )

    # --------------------------------------------------------
    # Filter definitions
    # --------------------------------------------------------

    all_filters = make_filters()

    dubai_filter = make_filters(
        emirates=[
            "Dubai"
        ]
    )

    abu_dhabi_filter = make_filters(
        emirates=[
            "Abu Dhabi"
        ]
    )

    store_1_filter = make_filters(
        store_ids=[
            1
        ]
    )

    store_7_filter = make_filters(
        store_ids=[
            7
        ]
    )

    year_2025_filter = make_filters(
        start_date=date(
            2025,
            1,
            1,
        ),
        end_date=date(
            2025,
            12,
            31,
        ),
    )

    # ========================================================
    # 2. CEO scope
    # ========================================================

    print(
        "\n[2] CEO FULL SCOPE"
    )

    ceo_stores = (
        get_filtered_store_performance(
            ceo,
            all_filters,
        )
    )

    ceo_emirates = (
        get_filtered_emirate_performance(
            ceo,
            all_filters,
        )
    )

    failures += check(
        len(
            ceo_stores
        )
        == 25,
        "CEO sees all 25 stores",
    )

    failures += check(
        len(
            ceo_emirates
        )
        == 7,
        "CEO sees all 7 emirates",
    )

    # ========================================================
    # 3. Dubai Manager scope
    # ========================================================

    print(
        "\n[3] DUBAI MANAGER RLS"
    )

    dubai_stores = (
        get_filtered_store_performance(
            dubai,
            all_filters,
        )
    )

    failures += check(
        len(
            dubai_stores
        )
        == 7,
        "Dubai Manager sees 7 stores",
    )

    failures += check(
        set(
            dubai_stores[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        "Dubai Manager sees Dubai only",
    )

    # ========================================================
    # 4. Store Manager scope
    # ========================================================

    print(
        "\n[4] STORE MANAGER RLS"
    )

    manager_stores = (
        get_filtered_store_performance(
            store_manager,
            all_filters,
        )
    )

    failures += check(
        len(
            manager_stores
        )
        == 1,
        "Store Manager sees one store",
    )

    failures += check(
        (
            not manager_stores.empty
            and manager_stores.iloc[
                0
            ][
                "StoreCode"
            ]
            == "STR001"
        ),
        "Store Manager sees STR001 only",
    )

    # ========================================================
    # 5. Date filtering
    # ========================================================

    print(
        "\n[5] DATE FILTER"
    )

    ceo_full_summary = (
        get_filtered_summary(
            ceo,
            all_filters,
        )
    )

    ceo_2025_summary = (
        get_filtered_summary(
            ceo,
            year_2025_filter,
        )
    )

    failures += check(
        float(
            ceo_2025_summary[
                "Revenue"
            ]
            or 0
        )
        > 0,
        "2025 filter returns revenue",
    )

    failures += check(
        float(
            ceo_2025_summary[
                "Revenue"
            ]
            or 0
        )
        < float(
            ceo_full_summary[
                "Revenue"
            ]
            or 0
        ),
        (
            "2025 revenue is narrower "
            "than full history"
        ),
    )

    # ========================================================
    # 6. Emirate filter
    # ========================================================

    print(
        "\n[6] EMIRATE FILTER"
    )

    ceo_dubai_stores = (
        get_filtered_store_performance(
            ceo,
            dubai_filter,
        )
    )

    failures += check(
        len(
            ceo_dubai_stores
        )
        == 7,
        "CEO Dubai filter returns 7 stores",
    )

    failures += check(
        set(
            ceo_dubai_stores[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        "CEO Dubai filter contains Dubai only",
    )

    # ========================================================
    # 7. Store filter
    # ========================================================

    print(
        "\n[7] STORE FILTER"
    )

    store_one = (
        get_filtered_store_performance(
            ceo,
            store_1_filter,
        )
    )

    failures += check(
        len(
            store_one
        )
        == 1
        and store_one.iloc[
            0
        ][
            "StoreCode"
        ]
        == "STR001",
        "CEO Store filter returns STR001",
    )

    # ========================================================
    # 8. Filter bypass resistance
    # ========================================================

    print(
        "\n[8] FILTER BYPASS RESISTANCE"
    )

    dubai_attempt = (
        get_filtered_store_performance(
            dubai,
            abu_dhabi_filter,
        )
    )

    failures += check(
        dubai_attempt.empty,
        (
            "Dubai Manager cannot filter "
            "into Abu Dhabi"
        ),
    )

    manager_attempt = (
        get_filtered_store_performance(
            store_manager,
            store_7_filter,
        )
    )

    failures += check(
        manager_attempt.empty,
        (
            "Store Manager cannot filter "
            "into STR007"
        ),
    )

    # ========================================================
    # 9. Products
    # ========================================================

    print(
        "\n[9] PRODUCTS"
    )

    products_all = (
        get_filtered_product_performance(
            ceo,
            all_filters,
        )
    )

    products_dubai = (
        get_filtered_product_performance(
            ceo,
            dubai_filter,
        )
    )

    failures += check(
        not products_all.empty,
        "Full product dataset available",
    )

    failures += check(
        not products_dubai.empty,
        "Dubai product dataset available",
    )

    failures += check(
        float(
            products_dubai[
                "Revenue"
            ].sum()
        )
        < float(
            products_all[
                "Revenue"
            ].sum()
        ),
        (
            "Product revenue narrows "
            "under Dubai filter"
        ),
    )

    # ========================================================
    # 10. Customers
    # ========================================================

    print(
        "\n[10] CUSTOMERS / RFM"
    )

    customer_all = (
        get_filtered_customer_summary(
            ceo,
            all_filters,
        )
    )

    customer_dubai = (
        get_filtered_customer_summary(
            ceo,
            dubai_filter,
        )
    )

    dubai_customer_rls = (
        get_filtered_customer_summary(
            dubai,
            all_filters,
        )
    )

    failures += check(
        customer_all[
            "Customers"
        ]
        > 0,
        "Customer analytics returns data",
    )

    failures += check(
        customer_dubai[
            "Customers"
        ]
        < customer_all[
            "Customers"
        ],
        "Customer scope narrows for Dubai",
    )

    failures += check(
        almost_equal(
            customer_dubai[
                "Revenue"
            ],
            dubai_customer_rls[
                "Revenue"
            ],
        ),
        (
            "CEO Dubai customer revenue "
            "matches Dubai Manager RLS revenue"
        ),
    )

    # ========================================================
    # 11. Promotions
    # ========================================================

    print(
        "\n[11] PROMOTIONS"
    )

    promo_all = (
        get_promotion_kpis(
            ceo,
            all_filters,
        )
    )

    promo_dubai = (
        get_promotion_kpis(
            ceo,
            dubai_filter,
        )
    )

    dubai_promo_rls = (
        get_promotion_kpis(
            dubai,
            all_filters,
        )
    )

    failures += check(
        float(
            promo_all[
                "PromotedRevenue"
            ]
            or 0
        )
        > 0,
        "Promotion analytics returns data",
    )

    failures += check(
        float(
            promo_dubai[
                "PromotedRevenue"
            ]
            or 0
        )
        < float(
            promo_all[
                "PromotedRevenue"
            ]
            or 0
        ),
        (
            "Promotion revenue narrows "
            "under Dubai filter"
        ),
    )

    failures += check(
        almost_equal(
            promo_dubai[
                "PromotedRevenue"
            ],
            dubai_promo_rls[
                "PromotedRevenue"
            ],
        ),
        (
            "CEO Dubai promotion revenue "
            "matches Dubai Manager RLS"
        ),
    )

    # ========================================================
    # 12. Returns
    # ========================================================

    print(
        "\n[12] RETURNS"
    )

    returns_all = (
        get_filtered_returns(
            ceo,
            all_filters,
        )
    )

    returns_dubai = (
        get_filtered_returns(
            ceo,
            dubai_filter,
        )
    )

    failures += check(
        not returns_all.empty,
        "Returns dataset available",
    )

    failures += check(
        len(
            returns_dubai
        )
        < len(
            returns_all
        ),
        (
            "Returns dataset narrows "
            "under Dubai filter"
        ),
    )

    failures += check(
        set(
            returns_dubai[
                "EmirateName"
            ].unique()
        )
        == {
            "Dubai"
        },
        "Dubai return data contains Dubai only",
    )

    # ========================================================
    # 13. Inventory
    # ========================================================

    print(
        "\n[13] INVENTORY"
    )

    inventory_all = (
        get_filtered_inventory(
            ceo,
            all_filters,
        )
    )

    inventory_dubai = (
        get_filtered_inventory(
            ceo,
            dubai_filter,
        )
    )

    inventory_manager = (
        get_filtered_inventory(
            inventory_analyst,
            all_filters,
        )
    )

    failures += check(
        not inventory_all.empty,
        "Inventory snapshot available",
    )

    failures += check(
        len(
            inventory_dubai
        )
        < len(
            inventory_all
        ),
        (
            "Inventory narrows under "
            "Dubai geography filter"
        ),
    )

    failures += check(
        set(
            inventory_dubai[
                "EmirateName"
            ].unique()
        )
        == {
            "Dubai"
        },
        "Dubai inventory contains Dubai only",
    )

    failures += check(
        len(
            inventory_manager
        )
        == len(
            inventory_all
        ),
        (
            "Inventory Analyst ALL scope "
            "matches company inventory scope"
        ),
    )

    # ========================================================
    # 14. Targets
    # ========================================================

    print(
        "\n[14] TARGETS"
    )

    targets_all = (
        get_filtered_target_summary(
            ceo,
            all_filters,
        )
    )

    targets_2025 = (
        get_filtered_target_summary(
            ceo,
            year_2025_filter,
        )
    )

    target_dubai = (
        get_filtered_store_targets(
            ceo,
            dubai_filter,
        )
    )

    target_dubai_rls = (
        get_filtered_store_targets(
            dubai,
            all_filters,
        )
    )

    failures += check(
        float(
            targets_all[
                "RevenueTarget"
            ]
            or 0
        )
        > 0,
        "Target data available",
    )

    failures += check(
        0
        < float(
            targets_2025[
                "RevenueTarget"
            ]
            or 0
        )
        < float(
            targets_all[
                "RevenueTarget"
            ]
            or 0
        ),
        (
            "Target date filter narrows "
            "to 2025"
        ),
    )

    failures += check(
        len(
            target_dubai
        )
        == 7
        and set(
            target_dubai[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        "Dubai target filter returns 7 Dubai stores",
    )

    failures += check(
        set(
            target_dubai_rls[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        (
            "Dubai Manager target RLS "
            "returns Dubai only"
        ),
    )

    # ========================================================
    # 15. Export permissions
    # ========================================================

    print(
        "\n[15] SECURE EXPORT PERMISSIONS"
    )

    failures += check(
        ceo.has_permission(
            "EXPORT_DATA"
        ),
        "CEO has EXPORT_DATA",
    )

    failures += check(
        dubai.has_permission(
            "EXPORT_DATA"
        ),
        "Dubai Manager has EXPORT_DATA",
    )

    failures += check(
        store_manager.has_permission(
            "EXPORT_DATA"
        ),
        "Store Manager has EXPORT_DATA",
    )

    failures += check(
        inventory_analyst.has_permission(
            "EXPORT_DATA"
        ),
        "Inventory Analyst has EXPORT_DATA",
    )

    # ========================================================
    # 16. Filtered export source safety
    # ========================================================

    print(
        "\n[16] EXPORT SOURCE SAFETY"
    )

    # secure_csv_download() only renders data passed by
    # the dashboard. Verify representative export sources
    # are already narrowed before reaching the component.

    failures += check(
        set(
            ceo_dubai_stores[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        (
            "Store export source is "
            "already filter-scoped"
        ),
    )

    failures += check(
        set(
            returns_dubai[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        (
            "Return export source is "
            "already filter-scoped"
        ),
    )

    failures += check(
        set(
            inventory_dubai[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        (
            "Inventory export source is "
            "already filter-scoped"
        ),
    )

    failures += check(
        set(
            target_dubai[
                "EmirateName"
            ]
        )
        == {
            "Dubai"
        },
        (
            "Target export source is "
            "already filter-scoped"
        ),
    )

    # ========================================================
    # Final Result
    # ========================================================

    print(
        "\n"
        + "-" * 78
    )

    if failures:
        print(
            f"Failed checks: "
            f"{failures}"
        )

        print(
            "FINAL BI SECURITY / "
            "FILTER VERIFICATION: FAILED"
        )

        print(
            "=" * 78
        )

        raise SystemExit(1)

    print(
        "Failed checks: 0"
    )

    print(
        "FINAL BI SECURITY / "
        "FILTER VERIFICATION: PASSED"
    )

    print(
        "Dashboard phase verified:"
    )

    print(
        "- RLS scope enforced"
    )

    print(
        "- Date filters enforced"
    )

    print(
        "- Emirate filters enforced"
    )

    print(
        "- Store filters enforced"
    )

    print(
        "- Cross-scope filter bypass rejected"
    )

    print(
        "- Products filter-aware"
    )

    print(
        "- Customers/RFM filter-aware"
    )

    print(
        "- Promotions filter-aware"
    )

    print(
        "- Returns filter-aware"
    )

    print(
        "- Inventory geography filter-aware"
    )

    print(
        "- Targets filter-aware"
    )

    print(
        "- Export sources RLS/filter scoped"
    )

    print(
        "=" * 78
    )


if __name__ == "__main__":
    main()