from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
import streamlit as st

from src.analytics.app_data import (
    get_data_bounds,
    get_visible_stores,
)


@dataclass(frozen=True)
class DashboardFilters:
    start_date: date | None
    end_date: date | None
    emirates: tuple[str, ...]
    store_ids: tuple[int, ...]

    @property
    def has_geography_filter(self) -> bool:
        return bool(
            self.emirates
            or self.store_ids
        )


def render_global_filters(
    user,
) -> DashboardFilters:
    stores = get_visible_stores(
        user
    )

    try:
        bounds = get_data_bounds(
            user
        )

        min_date = (
            pd.Timestamp(
                bounds["MinDate"]
            ).date()
            if bounds["MinDate"]
            is not None
            else None
        )

        max_date = (
            pd.Timestamp(
                bounds["MaxDate"]
            ).date()
            if bounds["MaxDate"]
            is not None
            else None
        )

    except Exception:
        min_date = None
        max_date = None

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-section-label">
                ANALYTICAL FILTERS
            </div>
            """,
            unsafe_allow_html=True,
        )

        date_enabled = (
            min_date is not None
            and max_date is not None
        )

        use_date_filter = st.toggle(
            "Custom date range",
            value=False,
            disabled=not date_enabled,
            key="global_use_dates",
        )

        start_date = None
        end_date = None

        if (
            use_date_filter
            and date_enabled
        ):
            selected_dates = (
                st.date_input(
                    "Date range",
                    value=(
                        min_date,
                        max_date,
                    ),
                    min_value=min_date,
                    max_value=max_date,
                    key="global_dates",
                )
            )

            if isinstance(
                selected_dates,
                (
                    tuple,
                    list,
                ),
            ):
                if (
                    len(
                        selected_dates
                    )
                    >= 1
                ):
                    start_date = (
                        selected_dates[0]
                    )

                if (
                    len(
                        selected_dates
                    )
                    >= 2
                ):
                    end_date = (
                        selected_dates[1]
                    )

        emirates_available = (
            sorted(
                stores[
                    "EmirateName"
                ]
                .dropna()
                .unique()
                .tolist()
            )
            if not stores.empty
            else []
        )

        selected_emirates = (
            st.multiselect(
                "Emirate",
                emirates_available,
                key="global_emirates",
                placeholder=(
                    "All visible emirates"
                ),
            )
        )

        store_options = (
            stores.copy()
        )

        if selected_emirates:
            store_options = (
                store_options.loc[
                    store_options[
                        "EmirateName"
                    ].isin(
                        selected_emirates
                    )
                ]
            )

        store_lookup = {
            (
                f"{row.StoreCode} - "
                f"{row.StoreName}"
            ):
                int(row.StoreId)

            for row
            in store_options.itertuples()
        }

        selected_store_labels = (
            st.multiselect(
                "Store",
                list(
                    store_lookup.keys()
                ),
                key="global_stores",
                placeholder=(
                    "All visible stores"
                ),
            )
        )

        selected_store_ids = tuple(
            store_lookup[label]
            for label
            in selected_store_labels
        )

        if st.button(
            "Reset analytical filters",
            use_container_width=True,
            key="reset_global_filters",
        ):
            for key in [
                "global_use_dates",
                "global_dates",
                "global_emirates",
                "global_stores",
            ]:
                st.session_state.pop(
                    key,
                    None,
                )

            st.rerun()

    return DashboardFilters(
        start_date=start_date,
        end_date=end_date,
        emirates=tuple(
            selected_emirates
        ),
        store_ids=(
            selected_store_ids
        ),
    )