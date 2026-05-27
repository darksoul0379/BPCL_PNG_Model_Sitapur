"""
auth.py
=======
Authentication layer for the Sitapur PNG dashboard.

Functions
---------
check_password()
    Gate the app behind a username / password login screen.
    Uses HMAC-safe comparison against credentials in st.secrets["app_users"].
    Calls st.stop() when the user is NOT authenticated, so the rest of main.py
    never executes for unauthenticated visitors.
    Returns True (implicitly, by not stopping) when already logged in.

logout_user()
    Clear all auth session state and rerun to return to the login screen.
    Sets sidebar_force_reset = True so the sidebar JS re-initialises cleanly
    on the next login.

APP_USERS
    Dict of {username: password} loaded from st.secrets at import time.
    Passwords are compared with hmac.compare_digest() to prevent timing attacks.
    Passwords are never stored in plain text in session state.
"""

import hmac

import streamlit as st
import streamlit.components.v1 as components

from premium_theme import inject_premium_theme

# Load app users from Streamlit secrets (set in .streamlit/secrets.toml)
APP_USERS: dict = st.secrets.get("app_users", {})


def check_password() -> None:
    """
    Gate the app behind a login screen.

    If the user is already authenticated (session state flag is True), this
    function returns immediately and main.py continues loading.

    Otherwise it renders a styled login card, calls st.stop(), and the rest
    of main.py does not execute for this request.

    The on_click callback _password_entered validates credentials and sets
    st.session_state["password_correct"] = True on success, which causes
    Streamlit to rerun and skip past this gate on the next cycle.
    """
    def _password_entered():
        """Validate credentials and set session state flags (callback)."""
        username = st.session_state.get("auth_username", "").strip()
        password = st.session_state.get("auth_password", "")
        expected = APP_USERS.get(username)

        if username and expected and hmac.compare_digest(str(password), str(expected)):
            st.session_state["password_correct"] = True
            st.session_state["logged_in_user"]   = username
            # Never keep raw password in session state
            st.session_state.pop("auth_password", None)
        else:
            st.session_state["password_correct"] = False

    # ── Already logged in — nothing to do ────────────────────────────────────────
    if st.session_state.get("password_correct", False):
        return

    # ── Remove stale sidebar toggle from a previous session ──────────────────────
    components.html(
        """
        <script>
        (function(){
            const pdoc = window.parent.document;
            ['sb-toggle-injected', 'sb-toggle-style'].forEach(id => {
                const el = pdoc.getElementById(id);
                if (el) el.remove();
            });
            const sidebar = pdoc.querySelector('[data-testid="stSidebar"]');
            const appView = pdoc.querySelector('[data-testid="stAppViewContainer"]');
            if (sidebar) {
                sidebar.style.transform  = 'translateX(0)';
                sidebar.style.pointerEvents = 'auto';
                sidebar.style.position   = '';
                sidebar.style.top        = '';
                sidebar.style.left       = '';
            }
            if (appView) {
                appView.style.removeProperty('grid-template-columns');
            }
        })();
        </script>
        """,
        height=0,
    )

    inject_premium_theme()

    # Centre the login card in the main content area
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] > .main {
            display:flex; align-items:center; justify-content:center; min-height:100vh;
        }
        [data-testid="stAppViewContainer"] > .main > div.block-container {
            max-width:560px; padding-top:0; padding-bottom:0;
        }
        .login-shell  { width:100%; display:flex; align-items:center;
                        justify-content:center; padding:1.5rem 0; background:transparent; }
        .login-card   { width:min(460px,100%); margin:0 auto;
                        background:rgba(8,15,32,0.82); backdrop-filter:blur(18px);
                        border:1px solid rgba(0,212,255,0.18); border-radius:24px;
                        box-shadow:0 18px 50px rgba(0,0,0,0.35); padding:28px 24px 22px; }
        .login-badge  { display:inline-flex; align-items:center; gap:8px; padding:8px 12px;
                        border-radius:999px; background:rgba(0,212,255,0.12);
                        border:1px solid rgba(0,212,255,0.22); color:#9be7ff;
                        font-size:0.82rem; font-weight:700; margin-bottom:14px; }
        .login-title  { font-size:2rem; font-weight:800; color:#f8fbff;
                        letter-spacing:-0.02em; margin:0 0 6px; }
        .login-sub    { color:#9fb3c8; font-size:0.98rem; line-height:1.6; margin-bottom:18px; }
        .login-help   { margin-top:14px; color:#7f93ab; font-size:0.85rem; }
        div[data-testid="stTextInput"] label { color:#c8d6e5 !important; font-weight:600 !important; }
        div[data-testid="stTextInput"] input {
            text-align:center; background:#ffffff !important;
            border:1px solid rgba(0,212,255,0.35) !important;
            color:#0a0f1e !important; border-radius:14px !important; font-weight:500 !important;
        }
        div[data-testid="stTextInput"] input::placeholder { color:#8a9ab5 !important; }
        div[data-testid="stButton"] > button {
            width:100%; border:none !important; border-radius:14px !important;
            background:linear-gradient(135deg,#00d4ff,#0099cc) !important;
            color:#fff !important; font-weight:700 !important;
            box-shadow:0 10px 28px rgba(0,153,204,.28) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-shell">
          <div class="login-card">
            <div class="login-badge">Secure Access</div>
            <div class="login-title">Sitapur PNG</div>
            <div class="login-sub">
              Field Intelligence Dashboard · BPCL<br/>
              Login to continue to your themed control panel.
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.text_input("Username", key="auth_username", placeholder="Enter your username")
    st.text_input("Password", type="password", key="auth_password",
                  placeholder="Enter your password")
    st.button("Login", on_click=_password_entered, type="primary")

    if st.session_state.get("password_correct") is False:
        st.error("Invalid username or password")

    st.markdown(
        "<div class='login-help'>Access is restricted to authorized dashboard users."
        "</div></div></div>",
        unsafe_allow_html=True,
    )
    st.stop()


def logout_user() -> None:
    """
    Log out the current user by clearing all auth-related session state.

    Sets sidebar_force_reset = True so the sidebar JS re-initialises cleanly
    after the next login (avoids a stale toggle button being left in the DOM).
    """
    st.session_state["password_correct"]    = False
    st.session_state["sidebar_force_reset"] = True
    for key in ("logged_in_user", "auth_username", "auth_password"):
        st.session_state.pop(key, None)
    st.rerun()
