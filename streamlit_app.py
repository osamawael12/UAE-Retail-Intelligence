from __future__ import annotations

import html
import inspect

import streamlit as st

from app.components import (
    app_topbar,
    filter_summary,
)
from app.filters import (
    render_global_filters,
)
from app.pages import (
    customers,
    executive,
    inventory,
    products,
    promotions,
    returns,
    sales,
    stores,
    targets,
)
from app.session import (
    get_current_user,
    login_user,
    logout_user,
)
from app.theme import (
    apply_theme,
)
from src.security.authentication import (
    authenticate,
)


# ============================================================
# Streamlit Configuration
# ============================================================

st.set_page_config(
    page_title=(
        "UAE Retail Intelligence"
    ),
    page_icon="UAE",
    layout="wide",
    initial_sidebar_state=(
        "expanded"
    ),
)

apply_theme()


# ============================================================
# Application Navigation
# ============================================================

PAGE_CONFIG = {
    "Executive Command Center": {
        "permission":
            "VIEW_EXECUTIVE",

        "renderer":
            executive.render,

        "description":
            (
                "Enterprise KPI and "
                "growth intelligence"
            ),
    },

    "Sales & Growth": {
        "permission":
            "VIEW_SALES",

        "renderer":
            sales.render,

        "description":
            (
                "Revenue, growth and "
                "commercial trends"
            ),
    },

    "Stores & Emirates": {
        "permission":
            "VIEW_STORES",

        "renderer":
            stores.render,

        "description":
            (
                "Store and UAE geographic "
                "performance"
            ),
    },

    "Products & Categories": {
        "permission":
            "VIEW_PRODUCTS",

        "renderer":
            products.render,

        "description":
            (
                "Merchandise, ABC and "
                "Pareto intelligence"
            ),
    },

    "Customers & RFM": {
        "permission_any": {
            "VIEW_CUSTOMERS",
            "VIEW_RFM",
        },

        "renderer":
            customers.render,

        "description":
            (
                "Customer value, RFM "
                "and retention"
            ),
    },

    "Promotions & Campaigns": {
        "permission":
            "VIEW_SALES",

        "renderer":
            promotions.render,

        "description":
            (
                "Campaign and discount "
                "intelligence"
            ),
    },

    "Returns Intelligence": {
        "permission":
            "VIEW_RETURNS",

        "renderer":
            returns.render,

        "description":
            (
                "Post-sale risk and "
                "return diagnostics"
            ),
    },

    "Inventory Control": {
        "permission":
            "VIEW_INVENTORY",

        "renderer":
            inventory.render,

        "description":
            (
                "Inventory health and "
                "reorder risk"
            ),
    },

    "Targets & Achievement": {
        "permission":
            "VIEW_TARGETS",

        "renderer":
            targets.render,

        "description":
            (
                "Actual versus target "
                "performance"
            ),
    },
}


# ============================================================
# HTML Rendering Helper
# ============================================================

def render_html(
    content: str,
) -> None:
    """
    Render HTML without leading Markdown indentation.

    This avoids Streamlit interpreting HTML as a code block.
    """

    cleaned = "\n".join(
        line.strip()
        for line
        in content.splitlines()
        if line.strip()
    )

    st.markdown(
        cleaned,
        unsafe_allow_html=True,
    )


# ============================================================
# Authorization
# ============================================================

def can_access_page(
    user,
    config: dict,
) -> bool:
    """
    Determine whether the authenticated application user
    is allowed to see a navigation page.

    This controls application navigation only.

    SQL Server RLS remains the row-level security boundary.
    """

    required_permission = (
        config.get(
            "permission"
        )
    )

    if required_permission:
        return user.has_permission(
            required_permission
        )

    any_permissions = (
        config.get(
            "permission_any",
            set(),
        )
    )

    if any_permissions:
        return any(
            user.has_permission(
                permission
            )
            for permission
            in any_permissions
        )

    return False


def get_available_pages(
    user,
) -> dict:
    return {
        name: config

        for name, config
        in PAGE_CONFIG.items()

        if can_access_page(
            user,
            config,
        )
    }


# ============================================================
# Login Screen
# ============================================================

def render_login() -> None:
    left, center, right = (
        st.columns(
            [
                1.05,
                1.20,
                1.05,
            ]
        )
    )

    with center:
        st.write("")
        st.write("")

        render_html(
            (
                '<div class="dashboard-header">'
                '<div class="dashboard-eyebrow">'
                "UNITED ARAB EMIRATES"
                "</div>"
                '<div class="dashboard-title">'
                "UAE Retail Intelligence"
                "</div>"
                '<div class="dashboard-subtitle">'
                "Secure enterprise retail analytics "
                "for commercial, customer and "
                "operational decision-making."
                "</div>"
                "</div>"
            )
        )

        st.caption(
            "Authorized users only"
        )

        with st.form(
            "login_form",
            clear_on_submit=False,
        ):
            username = (
                st.text_input(
                    "Username",
                    placeholder=(
                        "Enter username"
                    ),
                )
            )

            password = (
                st.text_input(
                    "Password",
                    type="password",
                    placeholder=(
                        "Enter password"
                    ),
                )
            )

            submitted = (
                st.form_submit_button(
                    "Sign in",
                    use_container_width=True,
                )
            )

        if not submitted:
            return

        with st.spinner(
            "Authenticating..."
        ):
            user = authenticate(
                username=username,
                password=password,
            )

        if user is None:
            st.error(
                "Invalid username "
                "or password."
            )

            return

        login_user(
            user
        )

        st.rerun()


# ============================================================
# Sidebar Branding
# ============================================================

def render_sidebar_brand() -> None:
    render_html(
        (
            '<div class="uae-brand">'
            '<div class="uae-brand-title">'
            "UAE Retail Intelligence"
            "</div>"
            '<div class="uae-brand-subtitle">'
            "EXECUTIVE ANALYTICS"
            "</div>"
            '<div class="uae-flag-line">'
            '<span style="background:#CE1126"></span>'
            '<span style="background:#00843D"></span>'
            '<span style="background:#FFFFFF"></span>'
            '<span style="background:#101820"></span>'
            "</div>"
            "</div>"
        )
    )


# ============================================================
# Sidebar User Identity
# ============================================================

def render_sidebar_user(
    user,
) -> None:
    username = html.escape(
        str(
            user.username
        )
    )

    role_html = "".join(
        (
            '<span class="role-chip">'
            + html.escape(
                str(role)
            )
            + "</span>"
        )
        for role
        in sorted(
            user.roles
        )
    )

    render_html(
        (
            '<div class="sidebar-section-label">'
            "AUTHENTICATED USER"
            "</div>"
            '<div style="'
            "color:#F4F8FB;"
            "font-size:1rem;"
            "font-weight:720;"
            "margin-bottom:.45rem;"
            '">'
            f"{username}"
            "</div>"
            "<div>"
            f"{role_html}"
            "</div>"
        )
    )


# ============================================================
# Sidebar Navigation
# ============================================================

def render_navigation(
    user,
):
    pages = get_available_pages(
        user
    )

    render_html(
        (
            '<div class="sidebar-section-label">'
            "WORKSPACE"
            "</div>"
        )
    )

    if not pages:
        st.warning(
            "No pages are assigned "
            "to this account."
        )

        return (
            None,
            None,
        )

    selected_name = st.radio(
        "Application navigation",
        list(
            pages.keys()
        ),
        label_visibility=(
            "collapsed"
        ),
        key="app_navigation",
    )

    return (
        selected_name,
        pages[
            selected_name
        ],
    )


# ============================================================
# Sidebar
# ============================================================

def render_sidebar(
    user,
):
    with st.sidebar:
        render_sidebar_brand()

        render_sidebar_user(
            user
        )

        selected_name, page = (
            render_navigation(
                user
            )
        )

    # Global filters are rendered by their own module.
    # get_visible_stores() is RLS-aware, therefore users can
    # only select stores already visible to their SQL scope.
    filters = (
        render_global_filters(
            user
        )
    )

    with st.sidebar:
        st.divider()

        st.caption(
            "SQL Server Row-Level Security "
            "defines the maximum data scope. "
            "Analytical filters can only "
            "narrow that scope."
        )

        if st.button(
            "Sign out",
            use_container_width=True,
            key="application_logout",
        ):
            logout_user()

            st.rerun()

    return (
        selected_name,
        page,
        filters,
    )


# ============================================================
# Renderer Compatibility
# ============================================================

def page_accepts_filters(
    renderer,
) -> bool:
    """
    Detect whether a page currently exposes:

        render(user)

    or:

        render(user, filters)

    This allows us to migrate dashboards one file at a time
    without breaking pages that have not yet been upgraded.
    """

    try:
        signature = (
            inspect.signature(
                renderer
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return False

    parameters = list(
        signature.parameters.values()
    )

    positional = [
        parameter

        for parameter
        in parameters

        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    ]

    has_var_args = any(
        parameter.kind
        == inspect.Parameter.VAR_POSITIONAL

        for parameter
        in parameters
    )

    return (
        has_var_args
        or len(positional) >= 2
    )


# ============================================================
# Page Execution
# ============================================================

def render_page(
    user,
    page,
    filters,
) -> None:
    if page is None:
        st.warning(
            "No analytics page "
            "is available."
        )

        return

    renderer = page[
        "renderer"
    ]

    if page_accepts_filters(
        renderer
    ):
        renderer(
            user,
            filters,
        )

    else:
        renderer(
            user
        )


# ============================================================
# Workspace
# ============================================================

def render_workspace(
    user,
    page,
    filters,
) -> None:
    app_topbar(
        user
    )

    filter_summary(
        filters
    )

    try:
        render_page(
            user=user,
            page=page,
            filters=filters,
        )

    except Exception as exc:
        st.error(
            "The dashboard could not "
            "complete the requested analysis."
        )

        st.error(
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        with st.expander(
            "Technical traceback",
            expanded=True,
        ):
            st.exception(
                exc
            )


# ============================================================
# Main
# ============================================================

def main() -> None:
    user = (
        get_current_user()
    )

    if user is None:
        render_login()

        return

    (
        selected_name,
        page,
        filters,
    ) = render_sidebar(
        user
    )

    render_workspace(
        user=user,
        page=page,
        filters=filters,
    )


if __name__ == "__main__":
    main()