from __future__ import annotations

import html
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.theme import COLORS


def _render_html(content: str) -> None:
    """
    Render application HTML without leading indentation.

    Keeping generated HTML flush-left prevents Streamlit /
    Markdown from interpreting indented HTML as a code block.
    """
    cleaned = "\n".join(
        line.strip()
        for line in content.splitlines()
        if line.strip()
    )

    st.markdown(
        cleaned,
        unsafe_allow_html=True,
    )


def page_header(
    title: str,
    subtitle: str,
    eyebrow: str = "UAE RETAIL INTELLIGENCE",
) -> None:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_eyebrow = html.escape(eyebrow)

    content = (
        '<div class="dashboard-header">'
        f'<div class="dashboard-eyebrow">{safe_eyebrow}</div>'
        f'<div class="dashboard-title">{safe_title}</div>'
        f'<div class="dashboard-subtitle">{safe_subtitle}</div>'
        "</div>"
    )

    _render_html(content)


def app_topbar(user) -> None:
    username = html.escape(
        user.username
    )

    content = (
        '<div class="app-topbar">'
        '<div class="app-topbar-left">'
        "Workspace: "
        "<strong>UAE Retail Analytics</strong>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "User: "
        f"<strong>{username}</strong>"
        "</div>"
        '<div class="app-security-badge">'
        "RLS SECURED"
        "</div>"
        "</div>"
    )

    _render_html(content)


def filter_summary(
    filters,
) -> None:
    chips: list[str] = []

    if (
        filters.start_date is not None
        and filters.end_date is not None
    ):
        chips.append(
            "Date: "
            f"{filters.start_date} "
            "to "
            f"{filters.end_date}"
        )
    else:
        chips.append(
            "Date: Full history"
        )

    if filters.emirates:
        chips.append(
            "Emirates: "
            + ", ".join(
                filters.emirates
            )
        )
    else:
        chips.append(
            "Emirates: All visible"
        )

    if filters.store_ids:
        chips.append(
            "Stores selected: "
            f"{len(filters.store_ids)}"
        )
    else:
        chips.append(
            "Stores: All visible"
        )

    rendered_chips = "".join(
        (
            '<span class="filter-chip">'
            f"{html.escape(chip)}"
            "</span>"
        )
        for chip in chips
    )

    _render_html(
        '<div class="filter-summary">'
        f"{rendered_chips}"
        "</div>"
    )


def section_header(
    title: str,
    subtitle: str | None = None,
) -> None:
    safe_title = html.escape(
        title
    )

    subtitle_content = ""

    if subtitle:
        subtitle_content = (
            '<div class="section-heading-subtitle">'
            f"{html.escape(subtitle)}"
            "</div>"
        )

    content = (
        '<div class="section-heading">'
        '<div class="section-heading-title">'
        f"{safe_title}"
        "</div>"
        f"{subtitle_content}"
        "</div>"
    )

    _render_html(content)


def insight_card(
    label: str,
    value: str,
    note: str,
    tone: str = "gold",
) -> None:
    if tone not in {
        "green",
        "red",
        "gold",
    }:
        tone = "gold"

    safe_label = html.escape(
        str(label)
    )

    safe_value = html.escape(
        str(value)
    )

    safe_note = html.escape(
        str(note)
    )

    content = (
        f'<div class="insight-card {tone}">'
        '<div class="insight-label">'
        f"{safe_label}"
        "</div>"
        '<div class="insight-value">'
        f"{safe_value}"
        "</div>"
        '<div class="insight-note">'
        f"{safe_note}"
        "</div>"
        "</div>"
    )

    _render_html(content)


def money(
    value,
    compact: bool = True,
) -> str:
    numeric = _safe_float(
        value
    )

    if not compact:
        return (
            f"AED {numeric:,.2f}"
        )

    absolute = abs(
        numeric
    )

    if absolute >= 1_000_000_000:
        return (
            "AED "
            f"{numeric / 1_000_000_000:.2f}B"
        )

    if absolute >= 1_000_000:
        return (
            "AED "
            f"{numeric / 1_000_000:.2f}M"
        )

    if absolute >= 1_000:
        return (
            "AED "
            f"{numeric / 1_000:.1f}K"
        )

    return (
        f"AED {numeric:,.0f}"
    )


def number(
    value,
    compact: bool = False,
) -> str:
    numeric = _safe_float(
        value
    )

    if compact:
        if abs(
            numeric
        ) >= 1_000_000:
            return (
                f"{numeric / 1_000_000:.2f}M"
            )

        if abs(
            numeric
        ) >= 1_000:
            return (
                f"{numeric / 1_000:.1f}K"
            )

    return (
        f"{int(round(numeric)):,}"
    )


def percentage(
    value,
    decimals: int = 1,
    signed: bool = False,
) -> str:
    numeric = _safe_float(
        value
    )

    if signed:
        return (
            f"{numeric:+.{decimals}f}%"
        )

    return (
        f"{numeric:.{decimals}f}%"
    )


def delta_text(
    value,
) -> str:
    if value is None:
        return "N/A"

    try:
        if pd.isna(
            value
        ):
            return "N/A"

    except TypeError:
        pass

    return percentage(
        value,
        decimals=1,
        signed=True,
    )


def metric(
    container,
    label: str,
    value: str,
    delta=None,
    help_text: str | None = None,
) -> None:
    formatted_delta = None

    if delta is not None:
        try:
            if not pd.isna(
                delta
            ):
                formatted_delta = (
                    delta_text(
                        delta
                    )
                )

        except TypeError:
            formatted_delta = (
                delta_text(
                    delta
                )
            )

    container.metric(
        label,
        value,
        delta=formatted_delta,
        help=help_text,
    )


def style_figure(
    figure: go.Figure,
    height: int = 390,
    legend: bool = True,
) -> go.Figure:
    figure.update_layout(
        height=height,

        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),

        plot_bgcolor=(
            "rgba(0,0,0,0)"
        ),

        font={
            "color":
                COLORS["text"],

            "family":
                (
                    "Segoe UI, "
                    "Inter, Arial"
                ),

            "size":
                12,
        },

        title_font={
            "size":
                16,

            "color":
                COLORS["text"],
        },

        margin=dict(
            l=28,
            r=28,
            t=62,
            b=32,
        ),

        hoverlabel=dict(
            bgcolor=(
                COLORS[
                    "surface2"
                ]
            ),

            bordercolor=(
                COLORS[
                    "border"
                ]
            ),

            font_color=(
                COLORS[
                    "text"
                ]
            ),
        ),

        legend=dict(
            orientation="h",

            yanchor="bottom",
            y=1.02,

            xanchor="right",
            x=1,

            bgcolor=(
                "rgba(0,0,0,0)"
            ),
        ),

        showlegend=legend,
    )

    figure.update_xaxes(
        gridcolor=(
            "rgba(143,165,185,.08)"
        ),

        linecolor=(
            "rgba(143,165,185,.16)"
        ),

        zeroline=False,

        tickfont=dict(
            color=(
                COLORS["muted"]
            )
        ),

        title_font=dict(
            color=(
                COLORS["muted"]
            )
        ),
    )

    figure.update_yaxes(
        gridcolor=(
            "rgba(143,165,185,.08)"
        ),

        linecolor=(
            "rgba(143,165,185,.16)"
        ),

        zeroline=False,

        tickfont=dict(
            color=(
                COLORS["muted"]
            )
        ),

        title_font=dict(
            color=(
                COLORS["muted"]
            )
        ),
    )

    return figure


def secure_csv_download(
    user,
    dataframe: pd.DataFrame,
    label: str,
    file_name: str,
    key: str,
) -> None:
    """
    Render CSV export only when the authenticated user
    has EXPORT_DATA permission.

    The caller must pass data already obtained through
    the secure RLS-aware application data layer.
    """

    if not user.has_permission(
        "EXPORT_DATA"
    ):
        return

    csv_bytes = (
        dataframe.to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )

    st.download_button(
        label=label,
        data=csv_bytes,
        file_name=file_name,
        mime="text/csv",
        key=key,
        use_container_width=True,
    )


def dataframe_config() -> dict:
    return {
        "Revenue":
            st.column_config.NumberColumn(
                "Revenue",
                format="AED %.2f",
            ),

        "GrossProfit":
            st.column_config.NumberColumn(
                "Gross Profit",
                format="AED %.2f",
            ),

        "ActualRevenue":
            st.column_config.NumberColumn(
                "Actual Revenue",
                format="AED %.2f",
            ),

        "RevenueTarget":
            st.column_config.NumberColumn(
                "Revenue Target",
                format="AED %.2f",
            ),

        "RevenueVariance":
            st.column_config.NumberColumn(
                "Revenue Variance",
                format="AED %.2f",
            ),

        "AOV":
            st.column_config.NumberColumn(
                "AOV",
                format="AED %.2f",
            ),

        "GrossMarginPct":
            st.column_config.NumberColumn(
                "Margin %",
                format="%.2f%%",
            ),

        "ReturnRatePct":
            st.column_config.NumberColumn(
                "Return %",
                format="%.2f%%",
            ),

        "DiscountRatePct":
            st.column_config.NumberColumn(
                "Discount %",
                format="%.2f%%",
            ),

        "MoMRevenuePct":
            st.column_config.NumberColumn(
                "MoM %",
                format="%.2f%%",
            ),

        "YoYRevenuePct":
            st.column_config.NumberColumn(
                "YoY %",
                format="%.2f%%",
            ),

        "RevenueAchievementPct":
            st.column_config.NumberColumn(
                "Achievement %",
                format="%.2f%%",
            ),
    }


def safe_growth(
    current,
    previous,
) -> float | None:
    current_value = (
        _safe_float(
            current
        )
    )

    previous_value = (
        _safe_float(
            previous
        )
    )

    if previous_value == 0:
        return None

    return (
        (
            current_value
            - previous_value
        )
        / abs(
            previous_value
        )
        * 100.0
    )


def _safe_float(
    value,
) -> float:
    if value is None:
        return 0.0

    try:
        if pd.isna(
            value
        ):
            return 0.0

    except TypeError:
        pass

    try:
        numeric = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    if not math.isfinite(
        numeric
    ):
        return 0.0

    return numeric