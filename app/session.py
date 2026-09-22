from __future__ import annotations

import streamlit as st

from src.security.authentication import AuthenticatedUser


USER_KEY = "authenticated_user"


def get_current_user() -> AuthenticatedUser | None:
    return st.session_state.get(USER_KEY)


def login_user(user: AuthenticatedUser) -> None:
    st.session_state[USER_KEY] = user


def logout_user() -> None:
    st.session_state.pop(USER_KEY, None)


def require_user() -> AuthenticatedUser:
    user = get_current_user()

    if user is None:
        st.error("Authentication required.")
        st.stop()

    return user
