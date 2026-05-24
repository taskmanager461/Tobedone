from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Callable, TypeVar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

try:
    from frontend.components.api_client import APIClient
    from frontend.components.styles import get_theme_css, get_theme_tokens
    from frontend.components.translations import LANGUAGES, translate
    from frontend.components.ui import metric_card, modern_progress, task_card, goal_card, habit_card, hero_metrics, render_logo
    from frontend.services.insights import build_weekly_insight
    from frontend.services.notifications import build_time_notifications
except ModuleNotFoundError:
    from components.api_client import APIClient
    from components.styles import get_theme_css, get_theme_tokens
    from components.translations import LANGUAGES, translate
    from components.ui import metric_card, modern_progress, task_card, goal_card, habit_card, hero_metrics, render_logo
    from services.insights import build_weekly_insight
    from services.notifications import build_time_notifications

st.set_page_config(page_title=translate("en", "app_title"), page_icon="🎯", layout="wide")

MENU = {
    "tasks": "menu_tasks",
    "reports": "menu_reports",
    "weekly": "menu_weekly",
    "me": "menu_me",
    "settings": "menu_settings",
}
T = TypeVar("T")

@st.cache_data(ttl=60)
def cached_score_history(user_id: int, _client: APIClient):
    return _client.score_history(user_id)

@st.cache_data(ttl=300)
def cached_smart_insights(_client: APIClient):
    return _client.smart_insights()

@st.cache_data(ttl=300)
def cached_weekly_summary(_client: APIClient):
    return _client.weekly_summary()

@st.cache_data(ttl=10)
def cached_get_tasks(user_id: int, day: date, _client: APIClient):
    return _client.get_tasks(user_id, day)

@st.cache_data(ttl=10)
def cached_get_habits(day: date, _client: APIClient):
    return _client.get_habits(day)


def init_state() -> None:
    # Handle Navigation from Query Params
    query_menu = st.query_params.get("menu")
    if query_menu and query_menu in MENU:
        st.session_state.menu = query_menu

    if "initialized" in st.session_state:
        return

    st.session_state.initialized = True
    defaults = {
        "api_url": os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
        "user_id": None,
        "username": "",
        "name": "",
        "access_token": "",
        "dark_mode": False,
        "lang": "en",
        "menu": "tasks",
        "last_daily_summary": "",
        "notifications": [],
        "install_prompt_requested": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_client() -> APIClient:
    client = APIClient(st.session_state.api_url)
    client.set_token(st.session_state.access_token or None)
    return client


def t(key: str, **kwargs: str) -> str:
    return translate(st.session_state["lang"], key, **kwargs)


def add_notification(level: str, message: str) -> None:
    entry = {
        "at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "level": level,
        "message": message,
    }
    existing = st.session_state.notifications or []
    st.session_state.notifications = [entry, *existing][:80]


def safe_error(message: str) -> str:
    return f"{message} {t('error_contact_support')}"


def call_api(
    func: Callable[..., T],
    *args: Any,
    fallback_message: str | None = None,
    **kwargs: Any,
) -> tuple[T | None, str | None]:
    fallback = fallback_message or t("service_unavailable")
    try:
        return func(*args, **kwargs), None
    except requests.HTTPError as exc:
        detail = fallback
        try:
            detail = exc.response.json().get("detail", fallback)
        except Exception:
            detail = fallback
        return None, safe_error(detail)
    except requests.RequestException:
        return None, safe_error(fallback)
    except Exception:
        return None, safe_error(fallback)


def render_top_header() -> None:
    st.markdown(f"<div class='main-title'>{t('app_title')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='main-subtitle'>{t('app_subtitle')}</div>", unsafe_allow_html=True)


def inject_pwa_support() -> None:
    api_url = st.session_state.api_url.rstrip('/')
    components.html(
        f"""
        <script>
        (function () {{
          if (!window.parent) return;
          const doc = window.parent.document;
          if (!doc) return;

          // SEO and Professional Branding
          if (doc.title !== "Task Manager") {{
            doc.title = "Task Manager - Your Consistency Engine";
          }}
          
          if (!doc.querySelector('meta[name="description"]')) {{
            const meta = doc.createElement("meta");
            meta.name = "description";
            meta.content = "Task Manager - Μια εφαρμογή συνέπειας για τις υποσχέσεις που δίνετε στον εαυτό σας. Παρακολουθήστε το trust score σας καθημερινά.";
            doc.head.appendChild(meta);
          }}

          if (!doc.querySelector('meta[name="keywords"]')) {{
            const meta = doc.createElement("meta");
            meta.name = "keywords";
            meta.content = "task manager, self trust score, habits, productivity, consistency, εφαρμογή παραγωγικότητας";
            doc.head.appendChild(meta);
          }}
          
          // Add Meta tags for mobile
          if (!doc.querySelector('meta[name="apple-mobile-web-app-capable"]')) {{
            const m1 = doc.createElement("meta");
            m1.name = "apple-mobile-web-app-capable";
            m1.content = "yes";
            doc.head.appendChild(m1);
            
            const m2 = doc.createElement("meta");
            m2.name = "apple-mobile-web-app-status-bar-style";
            m2.content = "black-translucent";
            doc.head.appendChild(m2);
            
            const m3 = doc.createElement("meta");
            m3.name = "viewport";
            m3.content = "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover";
            doc.head.appendChild(m3);
          }}

          if (!doc.querySelector('link[rel="manifest"]')) {{
            const link = doc.createElement("link");
            link.rel = "manifest";
            link.href = "{api_url}/manifest.json";
            doc.head.appendChild(link);
          }}

          if ("serviceWorker" in navigator) {{
            window.addEventListener('load', function() {{
              navigator.serviceWorker.register("{api_url}/sw.js").then(function(reg) {{
                console.log('ServiceWorker registration successful');
                window.parent.swRegistration = reg;
              }}).catch(function(err) {{
                console.log('ServiceWorker registration failed: ', err);
              }});
            }});
          }}

          // PWA Install Prompt Logic
          window.parent.deferredPrompt = null;
          window.parent.addEventListener("beforeinstallprompt", function (e) {{
            e.preventDefault();
            window.parent.deferredPrompt = e;
            console.log("Install prompt captured");
          }});

          // Bottom Nav Communication (Alternative via URL)
          if (!window.parent._task_manager_listener_set) {{
            window.parent._task_manager_listener_set = true;
            window.parent.addEventListener("message", (event) => {{
              if (event.data.type === "change_menu_url") {{
                const menuKey = event.data.menu;
                console.log("Navigating to menu:", menuKey);
                const url = new URL(window.parent.location.href);
                url.searchParams.set("menu", menuKey);
                window.parent.history.pushState({{}}, "", url);
                window.parent.location.reload(); // Force reload to apply new menu from query params
              }}
            }});
          }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_bottom_nav() -> None:
    active_menu = st.session_state.menu
    
    # Define icons for each menu item
    icons = {
        "tasks": "fa-solid fa-list-check",
        "reports": "fa-solid fa-chart-pie",
        "weekly": "fa-solid fa-lightbulb",
        "me": "fa-solid fa-user-circle",
        "settings": "fa-solid fa-sliders"
    }
    
    items_html = ""
    for key, menu_key in MENU.items():
        is_active = "active" if active_menu == key else ""
        label = t(menu_key)
        icon = icons.get(key, "fa-solid fa-circle")
        items_html += f"""
        <div class="nav-item {is_active}" onclick="window.parent.postMessage({{type: 'change_menu_url', menu: '{key}'}}, '*')">
            <i class="{icon}"></i>
            <span>{label}</span>
        </div>
        """

    components.html(
        f"""
        <script>
        (function() {{
            const doc = window.parent.document;
            let nav = doc.querySelector('.bottom-nav');
            if (!nav) {{
                nav = doc.createElement('div');
                nav.className = 'bottom-nav';
                doc.body.appendChild(nav);
            }}
            nav.innerHTML = `{items_html}`;
            
            // Re-apply active class based on items_html
            // The active state is already handled by Streamlit rerun
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_install_button() -> None:
    st.markdown(
        f"""
        <div style="margin-top: 1rem; text-align: center;">
            <button id="pwa-install-btn" class="install-btn">
                <i class="fa-solid fa-mobile-screen-button" style="margin-right: 8px;"></i>
                {t("mobile_install")}
            </button>
            <div id="install-help-ios" style="display:none; font-size: 0.9rem; color: #64748b; margin-top: 12px; padding: 12px; background: rgba(56, 189, 248, 0.1); border-radius: 12px; border: 1px dashed #0ea5e9;">
                <i class="fa-solid fa-share-from-square"></i> {t("mobile_install_help_ios") if "mobile_install_help_ios" in LANGUAGES[st.session_state.lang] else "Tap Share and 'Add to Home Screen'"}
            </div>
            <div id="install-help-generic" style="display:none; font-size: 0.8rem; color: #64748b; margin-top: 8px; padding: 10px;">
                <i class="fa-solid fa-circle-info"></i> {t("mobile_install_help")}
            </div>
        </div>
        <script>
            (function() {{
                const doc = window.parent.document;
                const btn = doc.getElementById("pwa-install-btn") || document.getElementById("pwa-install-btn");
                const helpIos = doc.getElementById("install-help-ios") || document.getElementById("install-help-ios");
                const helpGeneric = doc.getElementById("install-help-generic") || document.getElementById("install-help-generic");
                
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;

                if (isStandalone) {{
                    if (btn) btn.style.display = "none";
                    return;
                }}

                if (btn) {{
                    btn.onclick = async function () {{
                        console.log("Install button clicked");
                        const p = window.parent && window.parent.deferredPrompt;
                        
                        if (isIOS) {{
                            if (helpIos) helpIos.style.display = "block";
                            return;
                        }}

                        if (!p) {{
                            console.log("Install prompt not available (deferredPrompt is null)");
                            if (helpGeneric) helpGeneric.style.display = "block";
                            return;
                        }}
                        
                        try {{
                            p.prompt();
                            const {{ outcome }} = await p.userChoice;
                            console.log("User response to install prompt:", outcome);
                            window.parent.deferredPrompt = null;
                        }} catch (err) {{
                            console.error("Error during installation:", err);
                        }}
                    }};
                }}
            }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_notifications(tasks: list[dict[str, Any]], score: dict[str, Any]) -> None:
    notices, summary_key = build_time_notifications(tasks, score, st.session_state.last_daily_summary, t)
    for level, msg in notices:
        if level == "warning":
            st.warning(msg)
        elif level == "summary":
            st.toast(msg)
        else:
            st.info(msg)
        add_notification(level, msg)
    st.session_state.last_daily_summary = summary_key


def render_achievements(score: dict[str, Any]) -> None:
    badges: list[str] = []
    streak = int(score.get("streak", 0))
    success_rate = float(score.get("success_rate", 0.0))

    if streak >= 3:
        badges.append("🔥 " + t("badge_streak_3"))
    if streak >= 7:
        badges.append("🚀 " + t("badge_streak_7"))
    if success_rate >= 0.8:
        badges.append("✅ " + t("badge_consistent"))
    if float(score.get("score", 0.0)) >= 40:
        badges.append("🏆 " + t("badge_high_score"))

    if badges:
        st.markdown(f"**{t('achievements')}**")
        for badge in badges:
            st.markdown(f"{badge}")


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### {t('nav')}")
        for key, menu_key in MENU.items():
            if st.button(
                t(menu_key),
                key=f"menu_{key}",
                use_container_width=True,
                type="primary" if st.session_state.menu == key else "secondary",
            ):
                st.session_state.menu = key
                st.rerun()

        st.markdown("---")
        selected_dark = st.toggle(t("dark_mode"), value=st.session_state.dark_mode, key="sidebar_dark_mode")
        if selected_dark != st.session_state.dark_mode:
            st.session_state.dark_mode = selected_dark
            st.toast(t("theme_updated"))
            st.rerun()

        selected_language = st.selectbox(
            t("language"),
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state["lang"]),
            format_func=lambda code: LANGUAGES[code],
            key="sidebar_language",
        )
        if selected_language != st.session_state["lang"]:
            st.session_state["lang"] = selected_language
            print(f"[i18n] Language changed to: {selected_language}")
            st.toast(t("language_updated"))
            st.rerun()

        st.markdown("---")
        st.markdown(f"### {t('profile')}")
        if st.session_state.user_id:
            st.markdown(f"**{st.session_state.name}**")
            st.caption(f"@{st.session_state.username}")
            mode = t("theme_dark") if st.session_state.dark_mode else t("theme_light")
            st.caption(t("theme_mode", mode=mode))
            render_install_button()
        else:
            st.caption(t("please_login"))


def render_auth(client: APIClient) -> None:
    render_logo(st.session_state.dark_mode)
    
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    tab_login, tab_signup = st.tabs([t('sign_in'), t('create_account')])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            identifier = st.text_input(t("username_or_email"), placeholder=t("username_or_email"), label_visibility="collapsed")
            password = st.text_input(t("password"), type="password", placeholder=t("password"), label_visibility="collapsed")
            submitted = st.form_submit_button(t("sign_in"), type="primary")
            if submitted:
                data, err = call_api(
                    client.login,
                    username=identifier,
                    password=password,
                    fallback_message=t("login_failed"),
                )
                if err:
                    st.error(err)
                elif data:
                    st.session_state.user_id = data["user_id"]
                    st.session_state.username = data["username"]
                    st.session_state.name = data["name"]
                    st.session_state.access_token = data.get("access_token", "")
                    st.session_state.menu = "tasks"
                    st.toast(t("logged_in_success"))
                    st.rerun()

    with tab_signup:
        with st.form("signup_form", clear_on_submit=False):
            name = st.text_input(t("full_name"), placeholder=t("full_name"), label_visibility="collapsed")
            username = st.text_input(t("username"), key="signup_username", placeholder=t("username"), label_visibility="collapsed")
            email = st.text_input(t("email"), placeholder=t("email"), label_visibility="collapsed")
            password = st.text_input(t("password"), type="password", key="signup_password", placeholder=t("password"), label_visibility="collapsed")
            submitted = st.form_submit_button(t("create_account"), type="primary")
            if submitted:
                data, err = call_api(
                    client.signup,
                    username=username,
                    email=email,
                    password=password,
                    name=name,
                    fallback_message=t("signup_failed"),
                )
                if err:
                    st.error(err)
                elif data:
                    st.session_state.user_id = data["user_id"]
                    st.session_state.username = data["username"]
                    st.session_state.name = data["name"]
                    st.session_state.access_token = data.get("access_token", "")
                    st.session_state.menu = "tasks"
                    st.toast(t("account_created"))
                    st.rerun()

    st.markdown("<div class='auth-separator'>or</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="google-btn">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="18" height="18">
            Continue with Google
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)


def load_day_bundle(
    client: APIClient,
    user_id: int,
    day: date,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]] | None, str | None]:
    score, score_err = call_api(
        client.compute_daily_score,
        user_id=user_id,
        day=day,
        fallback_message=t("could_not_compute_daily_score"),
    )
    if score_err:
        return None, None, score_err

    tasks, task_err = call_api(
        cached_get_tasks,
        user_id,
        day,
        client,
        fallback_message=t("could_not_load_tasks"),
    )
    if task_err:
        return None, None, task_err

    return score, tasks, None


def plot_score_trend(history_df: pd.DataFrame, dark_mode: bool) -> go.Figure:
    colors = get_theme_tokens(dark_mode)
    if history_df.empty:
        history_df = pd.DataFrame({"date": [date.today()], "score": [0.0]})

    fig = px.line(history_df, x="date", y="score", markers=True)
    fig.update_traces(line_color=colors["accent"], marker_color=colors["accent_2"], line_width=3)
    fig.update_layout(
        paper_bgcolor=colors["surface"],
        plot_bgcolor=colors["surface"],
        font_color=colors["text"],
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="",
        yaxis_title=t("score_axis"),
    )
    return fig


def plot_status_pie(tasks_df: pd.DataFrame, dark_mode: bool) -> go.Figure:
    colors = get_theme_tokens(dark_mode)
    pending_label = t("pending")
    completed_label = t("completed")
    failed_label = t("failed")
    color_map = {
        completed_label: "#22c55e",
        failed_label: "#ef4444",
        pending_label: colors["muted"],
    }
    if tasks_df.empty:
        tasks_df = pd.DataFrame({"status": [pending_label], "count": [1]})
    else:
        tasks_df["status"] = tasks_df["status"].map(lambda s: t(s) if isinstance(s, str) else pending_label)
        tasks_df = tasks_df["status"].value_counts().rename_axis("status").reset_index(name="count")

    fig = px.pie(tasks_df, values="count", names="status", hole=0.55, color="status", color_discrete_map=color_map)
    fig.update_layout(
        paper_bgcolor=colors["surface"],
        plot_bgcolor=colors["surface"],
        font_color=colors["text"],
        margin=dict(l=10, r=10, t=20, b=10),
        legend_title_text="",
    )
    return fig


def plot_category_success(category_stats: pd.DataFrame, dark_mode: bool) -> go.Figure:
    colors = get_theme_tokens(dark_mode)
    if category_stats.empty:
        category_stats = pd.DataFrame({"category": ["general"], "success_rate": [0.0]})

    fig = px.bar(category_stats, x="category", y="success_rate", text="success_rate", range_y=[0, 1])
    fig.update_traces(marker_color="#22c55e", texttemplate="%{text:.0%}", textposition="outside")
    fig.update_layout(
        paper_bgcolor=colors["surface"],
        plot_bgcolor=colors["surface"],
        font_color=colors["text"],
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis_tickformat=".0%",
        xaxis_title="",
        yaxis_title=t("success_rate_axis"),
    )
    return fig


def get_score_label(score: float) -> str:
    if score >= 100.0:
        return "Excellent"
    elif score >= 60.0:
        return "Good"
    elif score >= 30.0:
        return "Average"
    else:
        return "Low"


@st.fragment
def render_habits_section(client: APIClient, selected_day: date):
    st.markdown(f"<div class='section-title'>Today's Habits</div>", unsafe_allow_html=True)
    habits, habit_err = call_api(cached_get_habits, selected_day, client)
    if habit_err:
        st.warning(habit_err)
    elif habits:
        due_habits = [h for h in habits if h.get("is_due_today")]
        if due_habits:
            for habit in due_habits:
                habit_card(habit)
                col1, col2, _ = st.columns([1, 1, 2])
                with col1:
                    if st.button(f"✔ Done", key=f"habit_done_{habit['id']}"):
                        call_api(client.track_habit, habit_id=habit["id"], status="completed", day=selected_day)
                        st.cache_data.clear()
                        st.rerun()
                with col2:
                    if st.button(f"⏭ Skip", key=f"habit_skip_{habit['id']}"):
                        call_api(client.track_habit, habit_id=habit["id"], status="skipped", day=selected_day)
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.info("No habits scheduled for this day.")
    else:
        st.info("No habits created yet.")


@st.fragment
def render_reports_charts(selected_day: date, tasks, client: APIClient, user_id: int):
    # 3. Trust Score Table (Score over time & Status Mix)
    st.markdown(f"<div class='section-title'>Trust Score Table</div>", unsafe_allow_html=True)
    history, history_err = call_api(cached_score_history, user_id, client)
    if history_err:
        st.warning(history_err)
    else:
        hist_df = pd.DataFrame(history or [])
        charts_col1, charts_col2 = st.columns([2, 1])
        with charts_col1:
            st.markdown(f"**{t('score_over_time')}**")
            st.plotly_chart(plot_score_trend(hist_df, st.session_state.dark_mode), use_container_width=True, config={"displayModeBar": False})
        with charts_col2:
            st.markdown(f"**{t('status_mix')}**")
            st.plotly_chart(plot_status_pie(pd.DataFrame(tasks or []), st.session_state.dark_mode), use_container_width=True, config={"displayModeBar": False})


def reports_page(client: APIClient, user_id: int) -> None:
    st.markdown(f"<div class='section-title'>{t('menu_reports')}</div>", unsafe_allow_html=True)
    
    # 1. Calendar (Day Picker)
    selected_day = st.date_input(t("day"), value=date.today(), key="reports_day")
    
    # Load data for selected day
    score, tasks, err = load_day_bundle(client, user_id, selected_day)
    if err:
        st.error(err)
    
    # 2. Today's Habits (using fragment)
    render_habits_section(client, selected_day)

    st.markdown("---")

    # 3. Trust Score Table (using fragment)
    if score:
        render_reports_charts(selected_day, tasks, client, user_id)

    st.markdown("---")

    # 4. Weekly Summary (Comparison from weekly summary endpoint)
    st.markdown(f"<div class='section-title'>Weekly Summary</div>", unsafe_allow_html=True)
    weekly_summary, summary_err = call_api(cached_weekly_summary, client)
    if weekly_summary:
        current_week = weekly_summary["current_week"]
        success_change = weekly_summary["success_change"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("📋", "Total Tasks", str(current_week["total_tasks"]))
        with col2:
            metric_card("✅", "Completed", str(current_week["completed_tasks"]))
        with col3:
            metric_card("📈", "Success Rate", f"{current_week['success_rate']}%")
        with col4:
            metric_card("🔥", "Streak", str(current_week["streak"]))

        if success_change != 0:
            change_label = f"+{success_change}% improvement" if success_change > 0 else f"{success_change}% drop"
            st.info(f"Compared to last week: {change_label}")


@st.fragment
def render_me_hero(score, tasks, client: APIClient):
    # 1. Hero Metrics
    score_label = get_score_label(score["score"])
    hero_metrics(
        score_value=f"{score['score']:.1f}",
        score_label=score_label,
        streak_value=f"{score['streak']}",
        streak_sub=t("multiplier", value=str(score["multiplier"])),
        success_value=f"{score['success_rate'] * 100:.0f}%",
        success_sub=t("tasks_count", count=str(score["total_tasks"]))
    )

    # 2. Today's Progress
    st.markdown(f"<div class='section-title'>Daily Progress</div>", unsafe_allow_html=True)
    completed = sum(1 for task in tasks if task["status"] == "completed")
    modern_progress(t("today_completion"), (completed / len(tasks)) if tasks else 0.0, tone="auto")


@st.fragment
def render_me_achievements(score, tasks):
    # 3. Achievements & Notifications
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        render_achievements(score)
    with c2:
        st.markdown(f"**Notifications**")
        render_notifications(tasks, score)


def me_page(client: APIClient, user_id: int) -> None:
    st.markdown(f"<div class='section-title'>{t('menu_me')}</div>", unsafe_allow_html=True)
    
    # User Profile Section
    user_name = st.session_state.get("name", "User")
    username = st.session_state.get("username", "user")
    
    # Profile Header with Avatar
    st.markdown(
        f"""
        <div class="surface-card" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="margin-bottom: 1.5rem;">
                <img src="https://ui-avatars.com/api/?name={user_name}&background=0a86ff&color=fff&size=128&bold=true" 
                     style="border-radius: 50%; width: 120px; height: 120px; border: 4px solid #0a86ff; box-shadow: 0 8px 24px rgba(10, 134, 255, 0.2);">
            </div>
            <div style="font-size: 2.2rem; font-weight: 900; margin-bottom: 0.25rem; letter-spacing: -0.02em;">{user_name}</div>
            <div style="color: #64748b; font-size: 1.1rem; font-weight: 600; margin-bottom: 1.5rem;">@{username}</div>
            <div style="display: flex; justify-content: center; gap: 1rem;">
                <div class="badge" style="background: rgba(10, 134, 255, 0.1); color: #0a86ff; padding: 8px 16px; font-size: 0.9rem; border-radius: 99px; font-weight: 700;">
                    <i class="fa-solid fa-user-check" style="margin-right: 6px;"></i> Verified Profile
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Edit Profile Section (Expander)
    with st.expander("⚙️ Edit Profile Settings", expanded=False):
        with st.form("edit_profile_form"):
            new_name = st.text_input("Full Name", value=user_name)
            new_username = st.text_input("Username", value=username)
            submit_profile = st.form_submit_button("Update Profile", type="primary")
            if submit_profile:
                if new_name.strip() and new_username.strip():
                    data, err = call_api(client.update_profile, name=new_name.strip(), username=new_username.strip())
                    if err:
                        st.error(err)
                    else:
                        st.session_state.name = data["name"]
                        st.session_state.username = data["username"]
                        st.toast("Profile updated successfully!")
                        st.rerun()
                else:
                    st.error("Name and username cannot be empty")

    st.markdown("---")
    
    # Load today's data for hero metrics (Cached)
    score, tasks, err = load_day_bundle(client, user_id, date.today())
    if err:
        st.error(err)
        return
    assert score is not None and tasks is not None

    # Get missed tasks
    missed, missed_err = call_api(client.get_missed_tasks, fallback_message="Could not load missed tasks")
    missed_count = missed.get("count", 0) if missed else 0

    # Render Hero and Progress
    render_me_hero(score, tasks, client)

    # Missed tasks feedback
    if missed_count > 0:
        warning_msg = f"You missed {missed_count} task{'' if missed_count == 1 else 's'}"
        if score["streak"] > 0:
            warning_msg += ". You are at risk of losing your streak!"
        st.warning(warning_msg)

    # Render Achievements and Notifications
    render_me_achievements(score, tasks)


@st.fragment
def render_weekly_insights(client: APIClient, theme):
    # --- Load Smart Insights (Cached) ---
    smart_insights, insights_err = call_api(cached_smart_insights, client)
    if insights_err:
        st.warning(insights_err)
        return
    if not smart_insights:
        return

    # --- 1. FAILURE ANALYSIS ---
    if smart_insights.get("failure_analysis"):
        st.markdown(f"<div class='section-title'>🔍 Failure Analysis</div>", unsafe_allow_html=True)
        failure_analysis = smart_insights["failure_analysis"]
        if failure_analysis["top_failure_categories"] or failure_analysis["failure_hours"]:
            col1, col2 = st.columns(2)
            with col1:
                if failure_analysis["top_failure_categories"]:
                    st.markdown("**Categories with Highest Failure Rate**")
                    for item in failure_analysis["top_failure_categories"][:3]:
                        st.markdown(f"**{item['category']}**: {item['rate']}% failure rate")
            with col2:
                if failure_analysis["failure_hours"]:
                    st.markdown("**Most Common Failure Hours**")
                    for hour, count in failure_analysis["failure_hours"][:3]:
                        st.markdown(f"{hour:02d}:00 - {count} failed tasks")
            st.info("💡 Understanding when and where you fail helps you adjust your schedule and expectations!")
            st.markdown("---")
    
    # --- 2. SUCCESS PATTERNS ---
    if smart_insights.get("success_analysis"):
        st.markdown(f"<div class='section-title'>✨ Success Patterns</div>", unsafe_allow_html=True)
        success_analysis = smart_insights["success_analysis"]
        if success_analysis["top_success_categories"] or success_analysis["success_hours"]:
            col1, col2 = st.columns(2)
            with col1:
                if success_analysis["top_success_categories"]:
                    st.markdown("**Your Strongest Categories**")
                    for item in success_analysis["top_success_categories"][:3]:
                        st.markdown(f"**{item['category']}**: {item['rate']}% success rate")
            with col2:
                if success_analysis["success_hours"]:
                    st.markdown("**Most Productive Hours**")
                    for hour, count in success_analysis["success_hours"][:3]:
                        st.markdown(f"{hour:02d}:00 - {count} completed tasks")
            st.info("💡 Build on your strengths! Schedule important tasks during your productive hours!")
            st.markdown("---")

    # --- 7. KEY INSIGHTS ---
    st.markdown(f"<div class='section-title'>🔑 Key Insights & Recommendations</div>", unsafe_allow_html=True)
    insights = smart_insights.get("insights", [])
    suggestions = smart_insights.get("suggestions", [])
    if insights:
        st.markdown("**What your data is telling you:**")
        for insight_text in insights[:4]:
            st.markdown(f"• {insight_text}")
    if suggestions:
        st.markdown("**Recommendations:**")
        for suggestion in suggestions[:4]:
            st.markdown(f"• 💡 {suggestion}")


def weekly_report_page(client: APIClient, user_id: int) -> None:
    st.markdown(f"<div class='section-title'>{t('weekly_report')}</div>", unsafe_allow_html=True)
    end_day = st.date_input(t("week_ending"), value=date.today(), key="week_end")
    start_day = end_day - timedelta(days=6)
    st.caption(t("range_label", start=start_day.isoformat(), end=end_day.isoformat()))

    history, err = call_api(cached_score_history, user_id, client)
    if err:
        st.error(err)
        return

    hist_df = pd.DataFrame(history or [])
    all_days = pd.date_range(start=start_day, end=end_day)
    if hist_df.empty:
        weekly_df = pd.DataFrame({"date": all_days, "score": 0.0, "success_rate": 0.0})
    else:
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        weekly_df = hist_df[(hist_df["date"] >= pd.Timestamp(start_day)) & (hist_df["date"] <= pd.Timestamp(end_day))]
        weekly_df = weekly_df[["date", "score", "success_rate"]]
        weekly_df = weekly_df.set_index("date").reindex(all_days, fill_value=0.0).reset_index()
        weekly_df = weekly_df.rename(columns={"index": "date"})

    weekly_success = float(weekly_df["success_rate"].mean() * 100) if not weekly_df.empty else 0.0
    theme = get_theme_tokens(st.session_state.dark_mode)
    
    # --- Weekly Overview ---
    c1, c2 = st.columns(2)
    with c1:
        metric_card("📊", t("weekly_success"), f"{weekly_success:.1f}%", t("avg_completion_consistency"))
    with c2:
        metric_card("📈", t("weekly_avg_score"), f"{weekly_df['score'].mean():.1f}", t("mean_daily_score"))

    st.plotly_chart(plot_score_trend(weekly_df, st.session_state.dark_mode), use_container_width=True, config={"displayModeBar": False})
    
    # Render Insights via Fragment
    render_weekly_insights(client, theme)



@st.fragment
def render_tasks_list(tasks, client: APIClient):
    st.markdown(f"<div class='section-title'>{t('task_cards')}</div>", unsafe_allow_html=True)
    if not tasks:
        st.info(t("no_tasks_day"))
    for task in tasks:
        task_card(
            task,
            labels={
                "category": t("category"),
                "difficulty": t("difficulty"),
                "status": t("status_col"),
                "unknown_title": t("unknown_title"),
                "uncategorized": t("uncategorized"),
                "easy": t("difficulty_easy"),
                "medium": t("difficulty_medium"),
                "hard": t("difficulty_hard"),
                "pending": t("pending"),
                "completed": t("completed"),
                "failed": t("failed"),
            },
        )
        b1, b2, _ = st.columns([1.15, 1, 2.8])
        with b1:
            if st.button(f"✔ {t('complete')}", key=f"complete_{task['id']}", type="secondary"):
                _, update_err = call_api(client.update_task_status, task_id=task["id"], status="completed", fallback_message=t("update_task_failed"))
                if update_err:
                    st.error(update_err)
                else:
                    st.cache_data.clear()
                    st.toast(t("task_completed"))
                    st.rerun()
        with b2:
            if st.button(f"❌ {t('fail')}", key=f"fail_{task['id']}", type="secondary"):
                _, update_err = call_api(client.update_task_status, task_id=task["id"], status="failed", fallback_message=t("update_task_failed"))
                if update_err:
                    st.error(update_err)
                else:
                    st.cache_data.clear()
                    st.toast(t("task_failed_marked"))
                    st.rerun()


@st.fragment
def render_analytics_section(tasks, dark_mode):
    st.markdown(f"<div class='section-title'>{t('analytics')}</div>", unsafe_allow_html=True)
    if not tasks:
        st.info(t("add_tasks_unlock"))
        return

    df = pd.DataFrame(tasks)
    completed_count = int((df["status"] == "completed").sum())
    modern_progress(t("completion_rate"), completed_count / len(df), tone="auto")

    category_total = df.groupby("category").size().rename("total")
    category_completed = df[df["status"] == "completed"].groupby("category").size().rename("completed")
    category_stats = pd.concat([category_total, category_completed], axis=1).fillna(0)
    category_stats["success_rate"] = (category_stats["completed"] / category_stats["total"]).fillna(0.0)
    category_stats = category_stats.reset_index().rename(columns={"index": "category"})

    st.plotly_chart(plot_category_success(category_stats[["category", "success_rate"]], dark_mode), use_container_width=True, config={"displayModeBar": False})
    st.plotly_chart(plot_status_pie(df, dark_mode), use_container_width=True, config={"displayModeBar": False})
    
    # Data Table
    display_df = df.copy()
    display_df["difficulty"] = display_df["difficulty"].map(lambda val: t(f"difficulty_{val}"))
    display_df["status"] = display_df["status"].map(lambda val: t(val))
    st.dataframe(
        display_df[["title", "category", "difficulty", "status"]].rename(
            columns={
                "title": t("title_col"),
                "category": t("category_col"),
                "difficulty": t("difficulty_col"),
                "status": t("status_col"),
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def tasks_analytics_page(client: APIClient, user_id: int) -> None:
    st.markdown(f"<div class='section-title'>{t('tasks_analytics')}</div>", unsafe_allow_html=True)
    
    # Initialize active tab in session state if not exists
    if "tasks_goals_tab" not in st.session_state:
        st.session_state.tasks_goals_tab = "Tasks"
    
    # Create tab buttons with styling
    tab1, tab2 = st.columns(2)
    with tab1:
        if st.button("📋 Tasks", key="tab_tasks", use_container_width=True, type="primary" if st.session_state.tasks_goals_tab == "Tasks" else "secondary"):
            st.session_state.tasks_goals_tab = "Tasks"
            st.rerun()
    with tab2:
        if st.button("🎯 Goals", key="tab_goals", use_container_width=True, type="primary" if st.session_state.tasks_goals_tab == "Goals" else "secondary"):
            st.session_state.tasks_goals_tab = "Goals"
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.tasks_goals_tab == "Tasks":
        selected_day = st.date_input(t("task_day"), value=date.today(), key="task_day")

        with st.form("add_task"):
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                title = st.text_input(t("task_title"))
            with c2:
                category = st.text_input(t("category"), value=t("category_placeholder"))
            with c3:
                difficulty = st.selectbox(
                    t("difficulty"),
                    ["easy", "medium", "hard"],
                    format_func=lambda val: t(f"difficulty_{val}"),
                )
            submitted = st.form_submit_button(t("add_task"), type="primary")
            if submitted and title.strip():
                _, create_err = call_api(
                    client.create_task,
                    user_id=user_id,
                    title=title.strip(),
                    category=category.strip() or "general",
                    difficulty=difficulty,
                    day=selected_day,
                    fallback_message=t("task_create_failed"),
                )
                if create_err:
                    st.error(create_err)
                else:
                    st.toast(t("task_added"))
                    st.rerun()

        tasks, err = call_api(client.get_tasks, user_id=user_id, day=selected_day, fallback_message=t("could_not_load_tasks"))
        if err:
            st.error(err)
            return
        tasks = tasks or []

        left, right = st.columns([1.3, 1])
        with left:
            render_tasks_list(tasks, client)

        with right:
            render_analytics_section(tasks, st.session_state.dark_mode)
    
    else:
        # Goals Tab
        st.markdown(f"<div class='section-title'>Your Goals</div>", unsafe_allow_html=True)
        
        # Add Goal Form
        with st.form("add_goal"):
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1.5])
            with c1:
                goal_title = st.text_input("Goal Title")
            with c2:
                goal_category = st.text_input("Category", value="general")
            with c3:
                goal_deadline = st.date_input("Deadline", min_value=date.today())
            with c4:
                goal_type = st.selectbox("Goal Type", ["today", "tomorrow", "three_days", "one_week", "two_weeks", "one_month", "three_months", "six_months", "one_year", "one_year_plus"], format_func=lambda x: {
                    "today": "Today (High Priority)",
                    "tomorrow": "Tomorrow (High Priority)",
                    "three_days": "1-3 days (High Priority)",
                    "one_week": "1 week (Medium Priority)",
                    "two_weeks": "1-2 weeks (Medium Priority)",
                    "one_month": "1 month (Medium Priority)",
                    "three_months": "3 months (Low Priority)",
                    "six_months": "6 months (Low Priority)",
                    "one_year": "1 year (Low Priority)",
                    "one_year_plus": "1 year+ (Low Priority)"
                }[x])
            
            goal_submitted = st.form_submit_button("🎯 Create Goal", type="primary")
            if goal_submitted and goal_title.strip():
                _, goal_err = call_api(
                    client.create_goal,
                    title=goal_title.strip(),
                    category=goal_category.strip() or "general",
                    deadline=goal_deadline,
                    goal_type=goal_type,
                    fallback_message="Failed to create goal",
                )
                if goal_err:
                    st.error(goal_err)
                else:
                    st.toast("Goal created successfully!")
                    st.rerun()
        
        # Load and display goals
        goals, goals_err = call_api(client.get_goals, fallback_message="Could not load goals")
        if goals_err:
            st.error(goals_err)
            return
        goals = goals or []
        
        if not goals:
            st.info("No goals yet. Create your first goal above!")
        else:
            # Display goals in 2 columns
            goal_cols = st.columns(2)
            for idx, goal in enumerate(goals):
                with goal_cols[idx % 2]:
                    goal_card(goal)
                    
                    # Action buttons for the goal
                    b1, b2, b3, _ = st.columns([1, 1, 1, 1])
                    
                    # Only show complete and fail buttons if goal is active
                    if goal["status"] == "active":
                        with b1:
                            if st.button(f"✅ Complete", key=f"complete_goal_{goal['id']}", type="secondary"):
                                _, update_err = call_api(
                                    client.update_goal,
                                    goal_id=goal["id"],
                                    status="achieved",
                                    fallback_message="Failed to complete goal"
                                )
                                if update_err:
                                    st.error(update_err)
                                else:
                                    st.toast("🎉 Goal completed!")
                                    st.rerun()
                        with b2:
                            if st.button(f"❌ Fail", key=f"fail_goal_{goal['id']}", type="secondary"):
                                _, update_err = call_api(
                                    client.update_goal,
                                    goal_id=goal["id"],
                                    status="failed",
                                    fallback_message="Failed to mark goal as failed"
                                )
                                if update_err:
                                    st.error(update_err)
                                else:
                                    st.toast("Goal marked as failed!")
                                    st.rerun()
                    
                    with b3:
                        if st.button(f"🗑️ Delete", key=f"delete_goal_{goal['id']}", type="secondary"):
                            _, delete_err = call_api(
                                client.delete_goal,
                                goal_id=goal["id"],
                                fallback_message="Failed to delete goal"
                            )
                            if delete_err:
                                st.error(delete_err)
                            else:
                                st.toast("Goal deleted")
                                st.rerun()
                    
                    # Reflection modal for completed goals
                    if goal["status"] == "achieved" and (not goal.get("reflection_went_well") or not goal.get("reflection_didnt_go_well")):
                        with st.expander("💭 Add Reflection", expanded=False):
                            with st.form(f"reflection_{goal['id']}"):
                                went_well = st.text_area("What went well?", value=goal.get("reflection_went_well", ""))
                                didnt_go_well = st.text_area("What didn't go well?", value=goal.get("reflection_didnt_go_well", ""))
                                save_reflection = st.form_submit_button("Save Reflection")
                                if save_reflection:
                                    _, update_err = call_api(
                                        client.update_goal,
                                        goal_id=goal["id"],
                                        reflection_went_well=went_well,
                                        reflection_didnt_go_well=didnt_go_well,
                                        fallback_message="Failed to save reflection"
                                    )
                                    if update_err:
                                        st.error(update_err)
                                    else:
                                        st.toast("Reflection saved!")
                                        st.rerun()
                    
                    # Show existing reflection
                    elif goal["status"] == "achieved" and (goal.get("reflection_went_well") or goal.get("reflection_didnt_go_well")):
                        with st.expander("💭 Reflection", expanded=False):
                            if goal.get("reflection_went_well"):
                                st.markdown(f"**What went well:**\n{goal['reflection_went_well']}")
                            if goal.get("reflection_didnt_go_well"):
                                st.markdown(f"**What didn't go well:**\n{goal['reflection_didnt_go_well']}")


def notifications_page() -> None:
    st.markdown(f"<div class='section-title'>{t('notifications_center')}</div>", unsafe_allow_html=True)
    if st.button(t("simulated_push"), key="simulate_push", type="primary"):
        msg = f"{datetime.now().strftime('%H:%M')} - {t('notif_start_reminder', count='1')}"
        add_notification("push", msg)
        st.toast(t("push_sent"))

    entries = st.session_state.notifications or []
    if not entries:
        st.info(t("notification_empty"))
        return
    for item in entries:
        level_key = f"notif_level_{item['level']}"
        level_label = t(level_key)
        st.markdown(
            f"<div class='surface-card'><strong>{item['at']}</strong> [{level_label}]<br/>{item['message']}</div>",
            unsafe_allow_html=True,
        )


def settings_page() -> None:
    st.markdown(f"<div class='section-title'>{t('settings')}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        metric_card("👤", t("name"), st.session_state.name or "-")
    with col2:
        metric_card("🆔", t("username"), st.session_state.username or "-")

    st.markdown(f"<div class='section-title'>{t('preferences')}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        selected_dark = st.toggle(t("dark_mode"), value=st.session_state.dark_mode, key="settings_dark_mode")
        if selected_dark != st.session_state.dark_mode:
            st.session_state.dark_mode = selected_dark
            st.toast(t("theme_updated"))
            st.rerun()
    with c2:
        selected_language = st.selectbox(
            t("language"),
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state["lang"]),
            format_func=lambda code: LANGUAGES[code],
            key="settings_language",
        )
        if selected_language != st.session_state["lang"]:
            st.session_state["lang"] = selected_language
            st.toast(t("language_updated"))
            st.rerun()

    st.markdown(f"<div class='section-title'>{t('app_management')}</div>", unsafe_allow_html=True)
    render_install_button()

    st.markdown(f"<div class='section-title'>{t('account')}</div>", unsafe_allow_html=True)
    if st.button(t("logout"), type="primary"):
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.name = ""
        st.session_state.access_token = ""
        st.session_state.menu = "reports"
        st.toast(t("logged_out"))
        st.rerun()


def main() -> None:
    init_state()
    st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)
    inject_pwa_support()

    client = get_client()

    if not st.session_state.user_id:
        render_auth(client)
        return

    render_sidebar()
    render_bottom_nav()
    render_top_header()
    
    user_id = int(st.session_state.user_id)
    
    with st.spinner("🚀 Optimizing..."):
        if st.session_state.menu == "tasks":
            tasks_analytics_page(client, user_id)
        elif st.session_state.menu == "reports":
            reports_page(client, user_id)
        elif st.session_state.menu == "me":
            me_page(client, user_id)
        elif st.session_state.menu == "weekly":
            weekly_report_page(client, user_id)
        elif st.session_state.menu == "notifications":
            notifications_page()
        elif st.session_state.menu == "settings":
            settings_page()
        else:
            tasks_analytics_page(client, user_id)


if __name__ == "__main__":
    main()
