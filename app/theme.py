from __future__ import annotations

import streamlit as st


COLORS = {
    "bg": "#06101B",
    "bg_soft": "#091725",
    "surface": "#0D1C2B",
    "surface2": "#11263A",
    "surface3": "#173149",
    "border": "#203A53",
    "border_soft": "#183047",

    "text": "#F4F8FB",
    "muted": "#8FA5B9",
    "muted2": "#6F879C",

    "uae_red": "#CE1126",
    "uae_green": "#00843D",
    "uae_white": "#FFFFFF",
    "uae_black": "#101820",

    "gold": "#D6B34A",

    "primary": "#00A664",
    "secondary": "#D6B34A",
    "success": "#16A66A",
    "warning": "#F1B548",
    "danger": "#E04956",
    "info": "#3A9EE8",
}


EMIRATE_COLORS = {
    "Abu Dhabi": "#D6B34A",
    "Dubai": "#CE1126",
    "Sharjah": "#00843D",
    "Ajman": "#3A9EE8",
    "Umm Al Quwain": "#9874CC",
    "Ras Al Khaimah": "#E88A32",
    "Fujairah": "#26AAA5",
}


RFM_COLORS = {
    "Champions": "#00A664",
    "Loyal": "#3A9EE8",
    "Potential Loyalists": "#D6B34A",
    "Promising": "#79C784",
    "At Risk": "#E88A32",
    "Hibernating": "#CE1126",
}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #06101B;
            --surface: #0D1C2B;
            --surface-2: #11263A;
            --border: #203A53;
            --text: #F4F8FB;
            --muted: #8FA5B9;
            --red: #CE1126;
            --green: #00843D;
            --gold: #D6B34A;
        }

        html,
        body,
        [class*="css"] {
            font-family:
                "Segoe UI",
                "Inter",
                Arial,
                sans-serif;
        }

        .stApp {
            background:
                radial-gradient(
                    circle at 92% -5%,
                    rgba(0,132,61,.11),
                    transparent 24%
                ),
                radial-gradient(
                    circle at 8% 0%,
                    rgba(206,17,38,.07),
                    transparent 23%
                ),
                linear-gradient(
                    180deg,
                    #06101B 0%,
                    #081521 48%,
                    #06101B 100%
                );
            color: var(--text);
        }

        .block-container {
            max-width: 1600px;
            padding-top: 1.15rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    #07121E,
                    #091827
                );
            border-right:
                1px solid #203A53;
        }

        [data-testid="stSidebar"]::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
            background:
                linear-gradient(
                    180deg,
                    #CE1126 0 19%,
                    #00843D 19% 45%,
                    #FFFFFF 45% 70%,
                    #101820 70% 100%
                );
        }

        .uae-brand {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(
                    145deg,
                    rgba(17,38,58,.96),
                    rgba(8,21,33,.98)
                );
            border: 1px solid #203A53;
            border-radius: 17px;
            padding: 17px;
            margin-bottom: .9rem;
            box-shadow:
                0 13px 32px rgba(0,0,0,.17);
        }

        .uae-brand-title {
            color: #FFFFFF;
            font-size: 1.02rem;
            font-weight: 760;
            letter-spacing: -.01em;
        }

        .uae-brand-subtitle {
            color: #D6B34A;
            font-size: .66rem;
            font-weight: 750;
            letter-spacing: .13em;
            margin-top: .28rem;
        }

        .uae-flag-line {
            display: flex;
            width: 100%;
            height: 4px;
            border-radius: 999px;
            overflow: hidden;
            margin-top: .85rem;
        }

        .uae-flag-line span {
            width: 25%;
        }

        .sidebar-section-label {
            color: #71889C;
            font-size: .67rem;
            font-weight: 760;
            letter-spacing: .13em;
            margin:
                .85rem 0
                .55rem 0;
        }

        .role-chip {
            display: inline-block;
            color: #E7C961;
            background:
                rgba(214,179,74,.08);
            border:
                1px solid
                rgba(214,179,74,.28);
            padding: 4px 9px;
            margin:
                0 4px
                4px 0;
            border-radius: 999px;
            font-size: .7rem;
        }

        .app-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            border:
                1px solid
                rgba(32,58,83,.7);
            background:
                rgba(13,28,43,.58);
            border-radius: 14px;
            padding:
                10px 15px;
            margin-bottom: .85rem;
        }

        .app-topbar-left {
            color: #8FA5B9;
            font-size: .78rem;
        }

        .app-topbar-left strong {
            color: #F4F8FB;
        }

        .app-security-badge {
            display: inline-flex;
            align-items: center;
            color: #73D5A1;
            background:
                rgba(0,132,61,.09);
            border:
                1px solid
                rgba(0,132,61,.28);
            border-radius: 999px;
            padding:
                5px 10px;
            font-size: .7rem;
            font-weight: 700;
        }

        .dashboard-header {
            position: relative;
            overflow: hidden;
            border: 1px solid #203A53;
            border-radius: 19px;
            background:
                linear-gradient(
                    118deg,
                    rgba(13,28,43,.98),
                    rgba(17,38,58,.91)
                );
            padding:
                25px 29px
                23px 31px;
            margin-bottom: 1.25rem;
            box-shadow:
                0 18px 42px
                rgba(0,0,0,.15);
        }

        .dashboard-header::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
            background:
                linear-gradient(
                    180deg,
                    #CE1126,
                    #D6B34A,
                    #00843D
                );
        }

        .dashboard-header::after {
            content: "";
            position: absolute;
            width: 230px;
            height: 230px;
            right: -80px;
            top: -120px;
            border-radius: 50%;
            background:
                radial-gradient(
                    circle,
                    rgba(0,132,61,.12),
                    transparent 70%
                );
        }

        .dashboard-eyebrow {
            color: #D6B34A;
            font-size: .7rem;
            font-weight: 780;
            letter-spacing: .15em;
            margin-bottom: .5rem;
        }

        .dashboard-title {
            color: #FFFFFF;
            font-size: 2.05rem;
            line-height: 1.13;
            font-weight: 760;
            letter-spacing: -.025em;
        }

        .dashboard-subtitle {
            color: #8FA5B9;
            max-width: 1030px;
            line-height: 1.55;
            font-size: .94rem;
            margin-top: .48rem;
        }

        .filter-summary {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin:
                -.15rem 0
                1.2rem 0;
        }

        .filter-chip {
            display: inline-flex;
            align-items: center;
            color: #AFC2D2;
            background:
                rgba(17,38,58,.75);
            border:
                1px solid #203A53;
            border-radius: 999px;
            padding:
                5px 10px;
            font-size: .72rem;
        }

        [data-testid="stMetric"] {
            position: relative;
            overflow: hidden;
            min-height: 116px;
            background:
                linear-gradient(
                    145deg,
                    rgba(17,38,58,.96),
                    rgba(13,28,43,.96)
                );
            border:
                1px solid #203A53;
            border-radius: 15px;
            padding: 17px;
            box-shadow:
                0 12px 26px
                rgba(0,0,0,.11);
        }

        [data-testid="stMetric"]::after {
            content: "";
            position: absolute;
            left: 0;
            bottom: 0;
            width: 42%;
            height: 2px;
            background:
                linear-gradient(
                    90deg,
                    #00843D,
                    transparent
                );
        }

        [data-testid="stMetric"]:hover {
            border-color:
                rgba(214,179,74,.46);
            transform:
                translateY(-1px);
            transition:
                .18s ease;
        }

        [data-testid="stMetricLabel"] {
            color: #8FA5B9;
            font-weight: 610;
        }

        [data-testid="stMetricValue"] {
            color: #F4F8FB;
            font-weight: 740;
            letter-spacing: -.02em;
        }

        [data-testid="stMetricDelta"] {
            font-weight: 650;
        }

        .section-heading {
            border-left:
                3px solid #D6B34A;
            padding-left: 10px;
            margin:
                1.35rem 0
                .8rem 0;
        }

        .section-heading-title {
            color: #F4F8FB;
            font-size: 1.08rem;
            font-weight: 720;
        }

        .section-heading-subtitle {
            color: #8FA5B9;
            font-size: .81rem;
            line-height: 1.5;
            margin-top: .18rem;
        }

        .insight-card {
            min-height: 112px;
            background:
                linear-gradient(
                    145deg,
                    rgba(17,38,58,.86),
                    rgba(13,28,43,.9)
                );
            border:
                1px solid #203A53;
            border-radius: 14px;
            padding: 15px 17px;
        }

        .insight-card.green {
            border-left:
                4px solid #00843D;
        }

        .insight-card.red {
            border-left:
                4px solid #CE1126;
        }

        .insight-card.gold {
            border-left:
                4px solid #D6B34A;
        }

        .insight-label {
            color: #8FA5B9;
            font-size: .69rem;
            font-weight: 760;
            letter-spacing: .095em;
        }

        .insight-value {
            color: #FFFFFF;
            font-size: 1.3rem;
            font-weight: 750;
            margin-top: .35rem;
        }

        .insight-note {
            color: #71889C;
            font-size: .78rem;
            line-height: 1.4;
            margin-top: .3rem;
        }

        div[data-testid="stPlotlyChart"] {
            background:
                linear-gradient(
                    145deg,
                    rgba(13,28,43,.54),
                    rgba(9,23,37,.45)
                );
            border:
                1px solid
                rgba(32,58,83,.75);
            border-radius: 15px;
            padding: 5px;
        }

        div[data-testid="stDataFrame"] {
            border:
                1px solid #203A53;
            border-radius: 14px;
            overflow: hidden;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom:
                1px solid #203A53;
        }

        .stTabs [data-baseweb="tab"] {
            color: #8FA5B9;
            background:
                rgba(13,28,43,.6);
            border-radius:
                9px 9px 0 0;
            padding:
                7px 14px;
        }

        .stTabs [aria-selected="true"] {
            color: #FFFFFF;
            border-bottom:
                2px solid #D6B34A;
        }

        .stButton button,
        .stDownloadButton button {
            border-radius: 10px;
            border:
                1px solid #284966;
            transition:
                all .15s ease;
        }

        .stButton button:hover,
        .stDownloadButton button:hover {
            border-color: #D6B34A;
            color: #FFFFFF;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: #0D1C2B;
            border-color: #203A53;
        }

        h1,
        h2,
        h3,
        h4 {
            color: #F4F8FB;
        }

        hr {
            border-color: #203A53;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        [data-testid="stDecoration"] {
            background-image:
                linear-gradient(
                    90deg,
                    #CE1126,
                    #D6B34A,
                    #00843D
                );
        }

        @media (
            max-width: 900px
        ) {
            .dashboard-title {
                font-size: 1.58rem;
            }

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .app-topbar {
                display: block;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )