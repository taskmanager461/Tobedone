from __future__ import annotations


def get_theme_tokens(dark_mode: bool) -> dict[str, str]:
    if dark_mode:
        return {
            "bg": "#00040a",
            "surface": "#0a0f1a",
            "surface_soft": "#141b2d",
            "sidebar": "#050810",
            "text": "#f8fafc",
            "muted": "#94a3b8",
            "accent": "#0a86ff",
            "accent_2": "#00d2ff",
            "accent_3": "#0a86ff",
            "border": "#1e293b",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "shadow": "0 25px 50px rgba(0, 0, 0, 0.5)",
        }

    return {
        "bg": "#ffffff",
        "surface": "#ffffff",
        "surface_soft": "#f8fafc",
        "sidebar": "#f1f5f9",
        "text": "#0f172a",
        "muted": "#64748b",
        "accent": "#0a86ff",
        "accent_2": "#00d2ff",
        "accent_3": "#0a86ff",
        "border": "#e2e8f0",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "shadow": "0 20px 60px rgba(15, 23, 42, 0.08)",
    }


def get_theme_css(dark_mode: bool) -> str:
    c = get_theme_tokens(dark_mode)
    return f"""
    <style>
    /* Hide Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    div[data-testid="stStatusWidget"] {{visibility: hidden;}}
    [data-testid="stHeader"] {{background: transparent; height: 0;}}
    .stAppDeployButton {{display: none !important;}}
    
    .stApp {{
        background: {c["bg"]};
        color: {c["text"]};
        font-family: "Inter", "SF Pro Display", -apple-system, sans-serif;
    }}

    /* Global List Style Reset to remove dots/bullets */
    ul, li, li::before, ul::before, [data-testid="stForm"] ul, [data-testid="stForm"] li {{
        list-style-type: none !important;
        list-style: none !important;
        margin-left: 0 !important;
        padding-left: 0 !important;
        content: none !important;
    }}

    /* Main Container */
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1280px;
    }}
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 6rem !important;
        }}
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {c["sidebar"]};
        border-right: none;
    }}

    /* Title Styles */
    .main-title {{
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, {c["accent"]}, {c["accent_3"]});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .main-subtitle {{
        color: {c["muted"]};
        margin-bottom: 2rem;
        font-weight: 500;
        font-size: 1rem;
    }}
    .section-title {{
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 1rem;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }}

    /* === COMPLETELY NEW METRIC CARDS === */
    .hero-metric-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }}
    @media (max-width: 768px) {{
        .hero-metric-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    .hero-metric {{
        position: relative;
        border-radius: 28px;
        padding: 1.75rem 1.5rem;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
        display: flex;
        flex-direction: column;
        min-height: 240px;
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }}

    .hero-metric-bg {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 0;
        background-position: center;
        background-repeat: no-repeat;
        pointer-events: none;
    }}

    .hero-metric-content {{
        position: relative;
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
    }}

    .hero-metric:hover {{
        transform: translateY(-8px) scale(1.02);
    }}

    .hero-metric-icon {{
        width: 50px;
        height: 50px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    /* === BRAND NEW BADGE IMPLEMENTATION (FROM SCRATCH) === */
    .status-badge-container {{
        width: 150px;
        height: 90px;
        margin-top: -15px; 
        margin-left: -20px;
        display: block;
        background-repeat: no-repeat;
        background-size: contain !important;
        background-position: center !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        filter: brightness(1.1) contrast(1.2) saturate(1.4) blur(0.2px);
        position: relative;
        z-index: 1000;
    }}

    .hero-metric-label {{
        font-size: 0.85rem;
        font-weight: 600;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.5rem;
    }}

    .hero-metric-value {{
        font-size: 3rem;
        font-weight: 900;
        line-height: 1;
        letter-spacing: -0.04em;
        margin-bottom: 0.5rem;
    }}

    .hero-metric-sub {{
        font-size: 0.9rem;
        font-weight: 700;
        opacity: 0.95;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0,0,0,0.15);
        padding: 6px 12px;
        border-radius: 9999px;
        backdrop-filter: blur(10px);
    }}

    /* Surface Cards (for tasks, goals, etc.) */
    .surface-card {{
        background: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: {c["shadow"]};
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }}

    .surface-card:hover {{
        border-color: {c["accent"]}40;
        transform: translateY(-3px);
    }}

    /* Progress Bar */
    .modern-progress-wrapper {{
        margin: 1.5rem 0;
    }}
    .modern-progress-label {{
        font-weight: 700;
        margin-bottom: 0.75rem;
        font-size: 0.95rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .modern-progress {{
        height: 10px;
        background: {c["border"]};
        border-radius: 9999px;
        overflow: hidden;
    }}
    .modern-progress-fill {{
        height: 100%;
        border-radius: 9999px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    /* Auth Styling */
    .auth-card {{
        max-width: 450px;
        margin: 0 auto;
        padding: 2rem;
        background: {c["surface"]};
        border-radius: 24px;
        border: 1px solid {c["border"]};
        box-shadow: {c["shadow"]};
        min-height: 580px;
        display: flex;
        flex-direction: column;
        overflow: hidden !important;
    }}

    /* Tighten up form spacing to prevent scrolling */
    [data-testid="stForm"] {{
        border: none !important;
        padding: 0 !important;
    }}
    [data-testid="stForm"] > div {{
        gap: 0.5rem !important;
    }}
    div[data-testid="stTextInput"] {{
        margin-bottom: -0.5rem !important;
    }}

    /* Target Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {c["surface_soft"]};
        border-radius: 16px;
        padding: 4px;
        gap: 4px;
        border: 1px solid {c["border"]};
        margin-bottom: 2rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 44px;
        white-space: pre;
        background-color: transparent;
        border-radius: 12px;
        color: {c["muted"]};
        font-weight: 600;
        flex: 1;
        transition: all 0.3s ease;
        border: none;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {c["accent"]} !important;
        color: white !important;
        box-shadow: 0 4px 12px {c["accent"]}40;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}

    /* Input Fields */
    div[data-testid="stTextInput"] input {{
        background-color: {c["surface_soft"]} !important;
        border: 1px solid {c["border"]} !important;
        border-radius: 14px !important;
        padding: 12px 16px !important;
        color: {c["text"]} !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: {c["accent"]} !important;
        box-shadow: 0 0 0 2px {c["accent"]}20 !important;
    }}

    /* Buttons */
    button[kind="primary"] {{
        background: linear-gradient(135deg, {c["accent"]}, {c["accent_2"]}) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        color: white !important;
        width: 100% !important;
        height: 50px !important;
        box-shadow: 0 8px 20px {c["accent"]}40 !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px {c["accent"]}60 !important;
    }}

    /* Separator */
    .auth-separator {{
        display: flex;
        align-items: center;
        text-align: center;
        margin: 2rem 0;
        color: {c["muted"]};
        font-size: 0.85rem;
    }}
    .auth-separator::before, .auth-separator::after {{
        content: '';
        flex: 1;
        border-bottom: 1px solid {c["border"]};
    }}
    .auth-separator:not(:empty)::before {{ margin-right: 1rem; }}
    .auth-separator:not(:empty)::after {{ margin-left: 1rem; }}

    /* Google Button */
    .google-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 12px !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        margin-top: 0.5rem;
    }}
    .google-btn:hover {{
        background: #f8fafc !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12) !important;
        border-color: #cbd5e1 !important;
    }}

    /* Bottom Nav */
    .bottom-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 75px;
        background: {c["surface"]}ee;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid {c["border"]};
        display: none;
        grid-template-columns: repeat(5, 1fr);
        z-index: 999999;
        box-shadow: 0 -15px 40px rgba(0,0,0,0.1);
        padding-bottom: env(safe-area-inset-bottom);
    }}
    @media (max-width: 768px) {{
        .bottom-nav {{
            display: grid;
        }}
    }}
    .nav-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
        color: {c["muted"]};
        text-decoration: none;
        font-size: 0.7rem;
        font-weight: 700;
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    .nav-item.active {{
        color: {c["accent"]};
    }}
    .nav-item i {{
        font-size: 1.4rem;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {c["bg"]};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {c["border"]};
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {c["muted"]};
    }}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    """
