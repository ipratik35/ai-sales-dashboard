"""
AI Sales Analytics Dashboard
Built with Streamlit | MySQL | Groq API | Plotly
"""

import streamlit as st
from groq import Groq
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from dotenv import load_dotenv
from datetime import datetime
import os
import re

import sqlite3

# ── Load Environment Variables & Secrets ─────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "olist_retail.db") if "__file__" in locals() else "olist_retail.db"
USE_SQLITE = os.path.exists("olist_retail.db") or os.path.exists(SQLITE_DB_PATH)

DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME", "olist_retail")
}

# Full schema for AI prompt
DB_SCHEMA = """
Database: olist_retail (Brazilian E-Commerce — Real Data)

Table: customers
- customer_id (VARCHAR) — links to orders.customer_id
- customer_unique_id (VARCHAR)
- customer_zip_code_prefix (INT)
- customer_city (VARCHAR)
- customer_state (VARCHAR) — 2-letter state code like SP, RJ, MG

Table: orders
- order_id (VARCHAR) — primary key, links to order_items, order_payments, order_reviews
- customer_id (VARCHAR) — links to customers.customer_id
- order_status (VARCHAR) — delivered, shipped, canceled, etc.
- order_purchase_timestamp (DATETIME)
- order_approved_at (DATETIME)
- order_delivered_carrier_date (DATETIME)
- order_delivered_customer_date (DATETIME)
- order_estimated_delivery_date (DATETIME)

Table: order_items
- order_id (VARCHAR) — links to orders.order_id
- order_item_id (INT) — item sequence within order
- product_id (VARCHAR) — links to products.product_id
- seller_id (VARCHAR) — links to sellers.seller_id
- shipping_limit_date (DATETIME)
- price (FLOAT) — item price
- freight_value (FLOAT) — shipping cost

Table: order_payments
- order_id (VARCHAR) — links to orders.order_id
- payment_sequential (INT)
- payment_type (VARCHAR) — credit_card, boleto, voucher, debit_card
- payment_installments (INT)
- payment_value (FLOAT)

Table: order_reviews
- review_id (VARCHAR)
- order_id (VARCHAR) — links to orders.order_id
- review_score (INT) — 1 to 5
- review_comment_title (TEXT)
- review_comment_message (TEXT)
- review_creation_date (DATETIME)
- review_answer_timestamp (DATETIME)

Table: products
- product_id (VARCHAR) — primary key
- product_category_name (VARCHAR) — category in Portuguese
- product_name_lenght (INT)
- product_description_lenght (INT)
- product_photos_qty (INT)
- product_weight_g (INT)
- product_length_cm (INT)
- product_height_cm (INT)
- product_width_cm (INT)

Table: sellers
- seller_id (VARCHAR) — primary key
- seller_zip_code_prefix (INT)
- seller_city (VARCHAR)
- seller_state (VARCHAR) — 2-letter state code

Table: category_translation
- product_category_name (VARCHAR) — Portuguese name, links to products.product_category_name
- product_category_name_english (VARCHAR) — English translation

IMPORTANT NOTES:
- The dataset does NOT have a product_name column. In this real-world dataset, Olist anonymized products using 32-character hex product_id hashes.
- When the user asks for "products" or "top products", NEVER display raw product_id alone. ALWAYS create a human-readable product label:
  CONCAT(COALESCE(ct.product_category_name_english, 'Product'), ' (', SUBSTRING(p.product_id, 1, 6), ')') AS product_name
  (joining products with category_translation ON product_category_name).
- Always join with category_translation to get English category names.
- Revenue = SUM(price) from order_items (NOT from orders table)
- To count orders, use COUNT(DISTINCT o.order_id) from orders table
- To get payment info, JOIN with order_payments ON order_id
- To get review scores, JOIN with order_reviews ON order_id
- Dates are in order_purchase_timestamp column in orders table
"""

# ══════════════════════════════════════════════════════
# DESIGN SYSTEM — Single source of truth
# ══════════════════════════════════════════════════════

# Global Typography and Contrast Colors
# Global Typography and Contrast Colors
FONT_FAMILY = "Poppins, -apple-system, BlinkMacSystemFont, sans-serif"

# ── Color System ──────────────────────────────────────
# Categorical palette: cohesive blues, teals, and soft grays
CATEGORICAL_COLORS = ["#1F4E79", "#4A90E2", "#8AB4F8", "#C3D7FA", "#E2E8F0"]

# Sequential palette: standardized blue gradient
BLUE_SCALE = "Blues"

COLORS = {
    "bg":             "#F7F8FA",   # Page background (soft off-white)
    "surface":        "#FFFFFF",   # Cards, panels
    "border":         "#E2E8F0",   # Borders, dividers
    "text_primary":   "#1E293B",   # Headings, strong emphasis
    "text_dark":      "#2B2B2B",   # High-contrast solid dark gray for all chart text
    "text_secondary": "#555555",   # High-contrast secondary text
    "gridline":       "#E5E5E5",   # Faint light gray gridlines
    "accent":         "#4A90E2",   # Cohesive mid blue accent
    "accent_dark":    "#1F4E79",   # Deep navy blue
    "accent_hover":   "#2563EB",   # Button hover
    # Semantic delivery performance colors (muted, cohesive)
    "on_time":        "#4A90E2",   # Calming cohesive blue
    "late":           "#D97768",   # Soft muted coral (replaces harsh bright red)
    "not_delivered":  "#CBD5E1",   # Soft neutral gray
}

# Chart dimensions
CHART_HEIGHT = 430

# ── Global Plotly Template: custom_theme ──────────────
custom_theme = pio.templates["simple_white"]
custom_theme.layout.update(
    colorway=CATEGORICAL_COLORS,
    font=dict(
        family=FONT_FAMILY,
        size=12,
        color=COLORS["text_dark"],
    ),
    title=dict(
        font=dict(
            family=FONT_FAMILY,
            size=18,
            color=COLORS["text_dark"],
        ),
        x=0,
        xanchor="left",
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=CHART_HEIGHT,
    margin=dict(l=60, r=30, t=50, b=50),
    coloraxis=dict(
        colorscale=BLUE_SCALE,
        showscale=False,
    ),
    xaxis=dict(
        title_font=dict(family=FONT_FAMILY, size=14, color=COLORS["text_dark"]),
        tickfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        gridcolor=COLORS["gridline"],
        zeroline=False,
        linecolor=COLORS["border"],
    ),
    yaxis=dict(
        title_font=dict(family=FONT_FAMILY, size=14, color=COLORS["text_dark"]),
        tickfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        gridcolor=COLORS["gridline"],
        zeroline=False,
        linecolor=COLORS["border"],
    ),
    legend=dict(
        font=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
    ),
    hoverlabel=dict(
        bgcolor=COLORS["surface"],
        font_size=12,
        font_color=COLORS["text_dark"],
        bordercolor=COLORS["border"],
    ),
)
custom_theme.layout.colorscale.sequential = px.colors.sequential.Blues
pio.templates["custom_theme"] = custom_theme
pio.templates.default = "custom_theme"

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="AI Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ────────────────────────────────────────
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ── Typography & Base ────────────────── */
    html, body, [class*="css"], [class*="st-"], .stApp, p, h1, h2, h3, h4, h5, h6, label, input, button, textarea, select, li, div {{
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    .stApp {{
        background-color: {COLORS["bg"]};
        color: {COLORS["text_dark"]};
    }}

    /* ── Protect Streamlit Icons from Font Override (Snip 1 Fix) ── */
    [data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] span,
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-icons,
    span[translate="no"] {{
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    }}

    /* ── Hide ONLY Deploy Button and 3-Dots Menu (Snip 2 Fix) ── */
    #MainMenu,
    [data-testid="stMainMenu"],
    .stDeployButton,
    button[aria-label="Manage app"],
    button[aria-label="Settings"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    footer {{
        visibility: hidden !important;
        display: none !important;
    }}
    [data-testid="stDecoration"] {{
        display: none !important;
    }}

    /* ── Ensure Sidebar Re-open / Expand Button is ALWAYS Visible & Prominent ── */
    [data-testid="stSidebarCollapsedControl"] {{
        visibility: visible !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        margin: 6px 0 0 12px !important;
        padding: 6px 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
        cursor: pointer !important;
        z-index: 999999 !important;
    }}
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] span,
    [data-testid="stSidebarCollapsedControl"] * {{
        visibility: visible !important;
        color: #1E293B !important;
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    }}
    [data-testid="stSidebarCollapsedControl"]:hover {{
        background-color: #F1F5F9 !important;
        border-color: #3B82F6 !important;
    }}

    /* ── Sidebar Collapse Button (Inside open sidebar) ── */
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
    }}
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapseButton"] * {{
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        color: #64748B !important;
    }}

    /* ── Header ───────────────────────────── */
    header[data-testid="stHeader"] {{
        background-color: {COLORS["bg"]};
        border-bottom: 1px solid {COLORS["border"]};
        height: 3.25rem !important;
        display: flex !important;
        align-items: center !important;
    }}

    /* ── Sidebar Polish ───────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {COLORS["surface"]};
        border-right: 1px solid {COLORS["border"]};
        overflow-x: hidden !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
        overflow-x: hidden !important;
        padding: 1.25rem 1rem !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {COLORS["text_dark"]};
    }}
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {{
        color: {COLORS["text_primary"]} !important;
        font-weight: 600 !important;
    }}
    /* Hide horizontal scrollbar in sidebar */
    [data-testid="stSidebar"]::-webkit-scrollbar,
    [data-testid="stSidebarUserContent"]::-webkit-scrollbar {{
        width: 4px;
        height: 0px;
    }}

    /* ── Typography ───────────────────────── */
    h1 {{
        color: {COLORS["text_primary"]} !important;
        -webkit-text-fill-color: {COLORS["text_primary"]} !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
    }}
    h2, h3 {{
        color: {COLORS["text_primary"]} !important;
        font-weight: 600 !important;
    }}
    h5 {{
        color: {COLORS["text_secondary"]} !important;
        font-weight: 400 !important;
    }}
    p, span, li, div {{
        color: {COLORS["text_dark"]};
    }}

    /* ── Metric Cards (Middle Aligned / Centered) ── */
    [data-testid="stMetric"] {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        padding: 20px 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }}
    [data-testid="stMetric"] label,
    [data-testid="stMetricLabel"] {{
        color: {COLORS["text_secondary"]} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
    }}
    [data-testid="stMetric"] label *,
    [data-testid="stMetricLabel"] * {{
        text-align: center !important;
        justify-content: center !important;
    }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {COLORS["text_primary"]} !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
    }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] * {{
        text-align: center !important;
        justify-content: center !important;
    }}
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        color: {COLORS["text_secondary"]} !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
    }}
    [data-testid="stMetric"] [data-testid="stMetricDelta"] * {{
        text-align: center !important;
        justify-content: center !important;
    }}

    /* ── Tabs (Solid contrast for both active and inactive) ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background-color: #EAEFF5;
        padding: 4px;
        border-radius: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border-radius: 8px !important;
        padding: 9px 22px !important;
        border: none !important;
        font-weight: 500 !important;
    }}
    .stTabs [data-baseweb="tab"] *,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {{
        color: {COLORS["text_secondary"]} !important;
        opacity: 1 !important;
        font-size: 14px !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS["surface"]} !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
        border: none !important;
    }}
    .stTabs [aria-selected="true"] *,
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div {{
        color: {COLORS["text_primary"]} !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }}

    /* ── Input & Buttons ──────────────────── */
    .stTextInput input {{
        background-color: {COLORS["surface"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        font-size: 14px;
        padding: 12px 14px;
    }}
    .stTextInput input::placeholder {{
        color: {COLORS["text_secondary"]} !important;
    }}
    .stTextInput input:focus {{
        border-color: {COLORS["accent"]};
        box-shadow: 0 0 0 2px rgba(59,130,246,0.12);
    }}
    .stButton button {{
        background-color: {COLORS["accent"]};
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        padding: 11px 22px;
        width: 100%;
        transition: background-color 0.15s ease;
    }}
    .stButton button:hover {{
        background-color: {COLORS["accent_hover"]};
        color: #FFFFFF !important;
    }}
    .stButton button * {{
        color: #FFFFFF !important;
    }}

    /* ── Code Blocks (High Contrast Dark Slate + Bright Crisp White SQL Text) ── */
    [data-testid="stCodeBlock"],
    div[data-testid="stCodeBlock"] pre,
    .stCode,
    .stCode pre {{
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }}
    [data-testid="stCodeBlock"] code,
    [data-testid="stCodeBlock"] pre,
    [data-testid="stCodeBlock"] span,
    .stCode code,
    .stCode pre,
    .stCode span {{
        color: #F8FAFC !important;
        font-family: 'JetBrains Mono', Consolas, Monaco, monospace !important;
        font-size: 13.5px !important;
        line-height: 1.6 !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }}
    /* High contrast keyword styling */
    [data-testid="stCodeBlock"] .hljs-keyword,
    [data-testid="stCodeBlock"] .token.keyword,
    .stCode .hljs-keyword,
    .stCode .token.keyword {{
        color: #38BDF8 !important;
        -webkit-text-fill-color: #38BDF8 !important;
        font-weight: 600 !important;
    }}
    [data-testid="stCodeBlock"] .hljs-string,
    [data-testid="stCodeBlock"] .token.string,
    .stCode .hljs-string,
    .stCode .token.string {{
        color: #A5F3FC !important;
        -webkit-text-fill-color: #A5F3FC !important;
    }}
    [data-testid="stCodeBlock"] .hljs-number,
    [data-testid="stCodeBlock"] .token.number,
    .stCode .hljs-number,
    .stCode .token.number {{
        color: #FDE047 !important;
        -webkit-text-fill-color: #FDE047 !important;
    }}
    [data-testid="stCodeBlock"] button {{
        color: #94A3B8 !important;
    }}

    /* ── Data Tables ──────────────────────── */
    [data-testid="stDataFrame"] {{
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid {COLORS["border"]};
    }}

    /* ── Dividers ─────────────────────────── */
    hr {{
        border-color: {COLORS["border"]};
    }}

    /* ── Alerts ───────────────────────────── */
    .stAlert {{
        border-radius: 8px;
    }}

    /* ── Captions ─────────────────────────── */
    .stCaption, [data-testid="stCaption"] {{
        color: {COLORS["text_secondary"]} !important;
        font-size: 12px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# ── Database Helpers ──────────────────────────────────
def get_connection():
    """Returns an active database connection (SQLite if file exists, else MySQL)."""
    if USE_SQLITE:
        db_file = SQLITE_DB_PATH if os.path.exists(SQLITE_DB_PATH) else "olist_retail.db"
        conn = sqlite3.connect(db_file, check_same_thread=False)

        # Register MySQL compatibility functions inside SQLite
        def _date_format(val, fmt):
            if not val:
                return None
            val_str = str(val)[:19]
            fmt_py = fmt.replace('%Y', '%Y').replace('%m', '%m').replace('%d', '%d').replace('%H', '%H').replace('%i', '%M').replace('%s', '%S')
            try:
                dt = datetime.fromisoformat(val_str)
                return dt.strftime(fmt_py)
            except Exception:
                return str(val)[:7]

        conn.create_function("DATE_FORMAT", 2, _date_format)
        conn.create_function("date_format", 2, _date_format)
        conn.create_function("MONTH", 1, lambda val: int(str(val)[5:7]) if val and len(str(val)) >= 7 else None)
        conn.create_function("month", 1, lambda val: int(str(val)[5:7]) if val and len(str(val)) >= 7 else None)
        conn.create_function("YEAR", 1, lambda val: int(str(val)[:4]) if val and len(str(val)) >= 4 else None)
        conn.create_function("year", 1, lambda val: int(str(val)[:4]) if val and len(str(val)) >= 4 else None)
        conn.create_function("CONCAT", -1, lambda *args: "".join(str(a) if a is not None else "" for a in args))
        conn.create_function("concat", -1, lambda *args: "".join(str(a) if a is not None else "" for a in args))
        return conn
    else:
        return mysql.connector.connect(**DB_CONFIG)

def run_query(query):
    """Run a SQL query and return a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def get_single_value(query):
    """Run a query that returns a single value."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        return result
    finally:
        conn.close()

# ── Chart Uniformity Helper ───────────────────────────
def apply_chart_defaults(fig, hide_colorbar=True):
    """
    Enforces the unified design system on every figure:
    - Transparent backgrounds ('rgba(0,0,0,0)')
    - Solid dark gray fonts (#2B2B2B) for maximum contrast
    - Title size: 18px, Axis labels: 14px, Data/Tick labels: 12px
    - Faint light gray gridlines (#E5E5E5) with no harsh zero-lines
    """
    layout_updates = dict(
        template="custom_theme",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        title_font=dict(family=FONT_FAMILY, size=18, color=COLORS["text_dark"]),
        legend_font=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        height=CHART_HEIGHT,
    )
    if hide_colorbar:
        layout_updates["coloraxis_showscale"] = False

    fig.update_layout(**layout_updates)

    # Apply axis standards (if chart has axes)
    fig.update_xaxes(
        title_font=dict(family=FONT_FAMILY, size=14, color=COLORS["text_dark"]),
        tickfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        gridcolor=COLORS["gridline"],
        zeroline=False,
        linecolor=COLORS["border"],
    )
    fig.update_yaxes(
        title_font=dict(family=FONT_FAMILY, size=14, color=COLORS["text_dark"]),
        tickfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        gridcolor=COLORS["gridline"],
        zeroline=False,
        linecolor=COLORS["border"],
    )
    return fig

# ── AI Functions ──────────────────────────────────────
def ask_ai(user_question):
    """Convert user question to SQL, execute it, return results."""
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
    You are an expert SQL analyst.

    I have a MySQL database with the following schema:
    {DB_SCHEMA}

    The user is asking: {user_question}

    Your job:
    1. Convert this question into a valid MySQL query
    2. Return ONLY the SQL query — no explanation, no markdown, no backticks
    3. Only use SELECT statements — never DELETE, UPDATE, DROP
    4. Always use lowercase column names exactly as shown in schema
    5. Use proper JOINs when data comes from multiple tables
    6. For category names, JOIN with category_translation to get English names
    7. Raw product_id is an unreadable 32-character hash. When asked for products or top products, ALWAYS generate a readable product_name alias using: CONCAT(COALESCE(ct.product_category_name_english, 'Product'), ' (', SUBSTRING(p.product_id, 1, 6), ')') AS product_name
    8. Limit results to 20 rows max unless user specifies otherwise

    SQL query:
    """

    message = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    sql_query = message.choices[0].message.content.strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    conn = get_connection()
    try:
        df_result = pd.read_sql(sql_query, conn)
        return df_result, sql_query, None
    except Exception as e:
        return None, sql_query, str(e)
    finally:
        conn.close()

def get_ai_insight(user_question, df_result):
    """Get a one-line business insight from AI about the results."""
    client = Groq(api_key=GROQ_API_KEY)

    data_summary = df_result.head(10).to_string(index=False)

    prompt = f"""
    The user asked: {user_question}

    Here are the query results:
    {data_summary}

    Give ONE short business insight (2 sentences max) about this data.
    Be specific with numbers. Focus on what's actionable.
    Do NOT start with "Based on the data" or similar.
    Return ONLY the insight text, nothing else.
    """

    message = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    return message.choices[0].message.content.strip()

def pick_chart_type(df, user_question):
    """Smart chart selection based on data and question."""
    question_lower = user_question.lower()
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    text_cols = df.select_dtypes(include='object').columns.tolist()

    time_keywords = ["trend", "monthly", "daily", "weekly", "over time", "by month", "by year", "growth"]
    if any(kw in question_lower for kw in time_keywords):
        return "line"

    share_keywords = ["distribution", "share", "percentage", "proportion", "breakdown"]
    if any(kw in question_lower for kw in share_keywords) and len(df) <= 8:
        return "pie"

    if len(df) <= 6 and len(numeric_cols) == 1 and len(text_cols) == 1:
        return "pie"

    return "bar"

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<h3 style='text-align: center; margin-bottom: 2px;'>📊 Sales Assistant</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12.5px; color: #555555; text-align: center; margin-top: -6px; margin-bottom: 14px;'>Executive Analytics & AI Query Engine</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<h4 style='text-align: center; margin-bottom: 2px;'>Sample Questions</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #64748B; text-align: center; margin-bottom: 14px;'>Ask anything in the AI Assistant tab:</p>", unsafe_allow_html=True)

    sample_questions = [
        "Top 10 product categories by revenue?",
        "Monthly sales trend?",
        "Which state has the most customers?",
        "Average review score by category?",
        "What payment methods are most used?",
        "Top 5 sellers by total revenue?",
        "How many orders were canceled?",
        "Late delivery rate by state?",
    ]
    for q in sample_questions:
        st.markdown(
            f"<div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; font-size: 12.5px; color: #334155; text-align: center; display: flex; align-items: center; justify-content: center; min-height: 42px; line-height: 1.35;'>"
            f"{q}"
            f"</div>",
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════
st.title("AI Sales Analytics Dashboard")
st.markdown("##### Explore real e-commerce data with pre-built insights + AI-powered queries")
st.divider()

# ══════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["Business Insights", "AI Assistant", "Query History"])

# ══════════════════════════════════════════════════════
# TAB 1: BUSINESS INSIGHTS
# ══════════════════════════════════════════════════════
with tab1:

    # ── KPI Cards ─────────────────────────────────────
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    total_revenue = get_single_value("SELECT ROUND(SUM(price), 2) FROM order_items")
    total_orders = get_single_value("SELECT COUNT(DISTINCT order_id) FROM orders")
    avg_review = get_single_value("SELECT ROUND(AVG(review_score), 1) FROM order_reviews")
    total_customers = get_single_value("SELECT COUNT(DISTINCT customer_unique_id) FROM customers")

    if total_revenue >= 1_000_000:
        revenue_display = f"R$ {total_revenue / 1_000_000:.1f}M"
    elif total_revenue >= 1_000:
        revenue_display = f"R$ {total_revenue / 1_000:.0f}K"
    else:
        revenue_display = f"R$ {total_revenue:,.0f}"

    with col1:
        st.metric("Total Revenue", revenue_display)
    with col2:
        st.metric("Total Orders", f"{total_orders:,}")
    with col3:
        st.metric("Avg Review Score", f"{avg_review} / 5")
    with col4:
        st.metric("Unique Customers", f"{total_customers:,}")

    st.divider()

    # ── Row 1: Revenue Trend + Category Revenue ──────
    st.markdown("### Revenue Analysis")
    left, right = st.columns(2)

    with left:
        df_trend = run_query("""
            SELECT
                DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
                ROUND(SUM(oi.price), 2) AS revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY month
            ORDER BY month
        """)

        fig_trend = px.line(
            df_trend, x="month", y="revenue",
            title="Monthly Revenue Trend",
            markers=True,
            color_discrete_sequence=[COLORS["accent"]]
        )
        fig_trend.update_layout(xaxis_title="Month", yaxis_title="Revenue (R$)")
        apply_chart_defaults(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

    with right:
        df_category = run_query("""
            SELECT
                ct.product_category_name_english AS category,
                ROUND(SUM(oi.price), 2) AS revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN category_translation ct ON p.product_category_name = ct.product_category_name
            GROUP BY ct.product_category_name_english
            ORDER BY revenue DESC
            LIMIT 10
        """)

        fig_cat = px.bar(
            df_category, x="revenue", y="category",
            title="Top 10 Categories by Revenue",
            color="revenue",
            color_continuous_scale=BLUE_SCALE,
            orientation="h"
        )
        fig_cat.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(l=180, r=30, t=50, b=50),
        )
        apply_chart_defaults(fig_cat)
        st.plotly_chart(fig_cat, use_container_width=True)

    st.divider()

    # ── Row 2: Top States + Payment Methods ──────────
    st.markdown("### Customer & Payment Analysis")
    left2, right2 = st.columns(2)

    with left2:
        df_states = run_query("""
            SELECT
                c.customer_state AS state,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(oi.price), 2) AS revenue
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY c.customer_state
            ORDER BY revenue DESC
            LIMIT 10
        """)

        # Format revenue to match the 5M y-axis scale
        df_states["revenue_fmt"] = df_states["revenue"].apply(
            lambda x: f"R$ {x/1_000_000:.1f}M" if x >= 1_000_000 else f"R$ {x/1_000:.0f}K"
        )

        fig_states = px.bar(
            df_states, x="state", y="revenue",
            title="Top 10 States by Revenue",
            color="revenue",
            color_continuous_scale=BLUE_SCALE,
            text="revenue_fmt",
            custom_data=["total_orders", "revenue"]
        )
        fig_states.update_traces(
            textposition='outside',
            textfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
            hovertemplate="<b>State:</b> %{x}<br><b>Revenue:</b> R$ %{customdata[1]:,.2f}<br><b>Total Orders:</b> %{customdata[0]:,}<extra></extra>"
        )
        fig_states.update_layout(
            xaxis_title="State",
            yaxis_title="Revenue (R$)",
            yaxis=dict(range=[0, df_states["revenue"].max() * 1.15])  # Leave headroom for labels
        )
        apply_chart_defaults(fig_states)
        st.plotly_chart(fig_states, use_container_width=True)

    with right2:
        df_payments = run_query("""
            SELECT
                payment_type,
                COUNT(*) AS count,
                ROUND(SUM(payment_value), 2) AS total_value
            FROM order_payments
            WHERE payment_type != 'not_defined'
            GROUP BY payment_type
            ORDER BY total_value DESC
        """)

        df_payments["payment_type"] = df_payments["payment_type"].str.replace("_", " ").str.title()

        fig_pay = px.pie(
            df_payments, values="total_value", names="payment_type",
            title="Payment Methods by Value",
            color_discrete_sequence=CATEGORICAL_COLORS,
        )
        fig_pay.update_traces(
            textposition="outside",
            textfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        )
        apply_chart_defaults(fig_pay, hide_colorbar=False)
        st.plotly_chart(fig_pay, use_container_width=True)

    st.divider()

    # ── Row 3: Review Scores + Delivery Performance ──
    st.markdown("### Delivery & Review Analysis")
    left3, right3 = st.columns(2)

    with left3:
        df_reviews = run_query("""
            SELECT
                review_score,
                COUNT(*) AS count
            FROM order_reviews
            GROUP BY review_score
            ORDER BY review_score
        """)

        fig_rev = px.bar(
            df_reviews, x="review_score", y="count",
            title="Review Score Distribution",
            color="count",
            color_continuous_scale=BLUE_SCALE,
        )
        fig_rev.update_layout(
            xaxis_title="Review Score (1-5)",
            yaxis_title="Number of Reviews",
        )
        apply_chart_defaults(fig_rev)
        st.plotly_chart(fig_rev, use_container_width=True)

    with right3:
        df_delivery = run_query("""
            SELECT
                CASE
                    WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 'On Time'
                    WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 'Late'
                    ELSE 'Not Delivered'
                END AS delivery_status,
                COUNT(*) AS count
            FROM orders
            WHERE order_status = 'delivered'
            GROUP BY delivery_status
        """)

        fig_del = px.pie(
            df_delivery, values="count", names="delivery_status",
            title="Delivery Performance",
            color="delivery_status",
            color_discrete_map={
                "On Time": COLORS["on_time"],             # Calm cohesive blue (#4A90E2)
                "Late": COLORS["late"],                   # Soft muted coral (#D97768)
                "Not Delivered": COLORS["not_delivered"], # Soft neutral gray (#CBD5E1)
            },
        )
        fig_del.update_traces(
            textposition="outside",
            textfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
        )
        apply_chart_defaults(fig_del, hide_colorbar=False)
        st.plotly_chart(fig_del, use_container_width=True)

    # ── Insight: Late Delivery vs Review Score ────────
    st.markdown("### Key Insight: Late Deliveries Impact on Reviews")
    df_insight = run_query("""
        SELECT
            CASE
                WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time'
                ELSE 'Late'
            END AS delivery_status,
            ROUND(AVG(r.review_score), 2) AS avg_review_score,
            COUNT(*) AS total_orders
        FROM orders o
        JOIN order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
            AND o.order_delivered_customer_date IS NOT NULL
            AND o.order_estimated_delivery_date IS NOT NULL
        GROUP BY delivery_status
    """)

    col_a, col_b = st.columns(2)
    for _, row in df_insight.iterrows():
        if row["delivery_status"] == "On Time":
            with col_a:
                st.metric(
                    "On-Time Delivery — Avg Review",
                    f"{row['avg_review_score']} / 5",
                    f"{row['total_orders']:,} orders"
                )
        else:
            with col_b:
                st.metric(
                    "Late Delivery — Avg Review",
                    f"{row['avg_review_score']} / 5",
                    f"{row['total_orders']:,} orders"
                )

# ══════════════════════════════════════════════════════
# TAB 2: AI ASSISTANT
# ══════════════════════════════════════════════════════
with tab2:
    st.markdown("### Ask Any Question About the Data")
    st.markdown("Type your question in plain English — AI will write the SQL, run it, and show results.")

    user_question = st.text_input(
        "",
        placeholder="e.g. What are the top 5 product categories by total revenue?",
        key="ai_question"
    )

    if st.button("Ask AI", key="ask_btn"):
        if user_question:
            with st.spinner("AI is generating your query..."):
                df_result, sql_query, error = ask_ai(user_question)

            st.markdown("**Generated SQL:**")
            st.code(sql_query, language="sql")

            if error:
                st.error(f"Query Error: {error}")
            elif df_result is not None and len(df_result) > 0:

                # AI insight
                with st.spinner("Generating insight..."):
                    try:
                        insight = get_ai_insight(user_question, df_result)
                        st.info(f"**Insight:** {insight}")
                    except Exception:
                        pass

                # Results table
                st.markdown("**Results:**")
                st.dataframe(df_result, use_container_width=True)
                st.caption(f"{len(df_result)} rows returned")

                # Smart product label synthesis if both product_id and category exist
                cat_col = next((c for c in ['category', 'product_category_name_english', 'product_category_name'] if c in df_result.columns), None)
                if 'product_id' in df_result.columns and cat_col:
                    df_result['product'] = df_result[cat_col].fillna('Item').astype(str) + ' (#' + df_result['product_id'].astype(str).str[:6] + ')'

                # Smart chart column detection
                numeric_cols = df_result.select_dtypes(include='number').columns.tolist()
                text_cols = df_result.select_dtypes(include='object').columns.tolist()
                date_cols = df_result.select_dtypes(include='datetime').columns.tolist()

                if not date_cols and text_cols:
                    for col in list(text_cols):
                        sample = str(df_result[col].iloc[0]) if len(df_result) > 0 else ""
                        if re.match(r'\d{4}-\d{2}', sample):
                            date_cols.append(col)
                            text_cols.remove(col)
                            break

                if numeric_cols and (text_cols or date_cols):
                    chart_type = pick_chart_type(df_result, user_question)

                    # Prioritize human-friendly descriptive columns over raw hex IDs
                    id_pattern = re.compile(r'(_id|uuid|hash|^id$)', re.IGNORECASE)
                    descriptive_text_cols = [c for c in text_cols if not id_pattern.search(c)]

                    if date_cols:
                        x_col = date_cols[0]
                    elif 'product' in df_result.columns:
                        x_col = 'product'
                    elif 'product_name' in df_result.columns:
                        x_col = 'product_name'
                    elif descriptive_text_cols:
                        x_col = descriptive_text_cols[0]
                    else:
                        x_col = text_cols[0]
                        # Shorten unreadable 32-char hashes if only raw ID exists
                        if df_result[x_col].astype(str).str.len().max() > 12:
                            short_col = x_col + '_short'
                            df_result[short_col] = '#' + df_result[x_col].astype(str).str[:8]
                            x_col = short_col

                    y_col = numeric_cols[0]

                    st.markdown("### Visualization")

                    if chart_type == "line":
                        fig = px.line(
                            df_result, x=x_col, y=y_col,
                            title=user_question,
                            markers=True,
                            color_discrete_sequence=[COLORS["accent"]],
                        )
                    elif chart_type == "pie":
                        fig = px.pie(
                            df_result, values=y_col, names=x_col,
                            title=user_question,
                            color_discrete_sequence=CATEGORICAL_COLORS,
                        )
                        fig.update_traces(
                            textposition="outside",
                            textfont=dict(family=FONT_FAMILY, size=12, color=COLORS["text_dark"]),
                        )
                    else:
                        fig = px.bar(
                            df_result, x=x_col, y=y_col,
                            title=user_question,
                            color=y_col,
                            color_continuous_scale=BLUE_SCALE,
                        )

                    apply_chart_defaults(fig)
                    st.plotly_chart(fig, use_container_width=True)

                # Save to history
                st.session_state.query_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": user_question,
                    "sql": sql_query,
                    "rows": len(df_result),
                    "status": "Success"
                })

            elif df_result is not None and len(df_result) == 0:
                st.warning("Query ran successfully but returned no results.")
                st.session_state.query_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": user_question,
                    "sql": sql_query,
                    "rows": 0,
                    "status": "No Results"
                })
        else:
            st.warning("Please type a question first.")

# ══════════════════════════════════════════════════════
# TAB 3: QUERY HISTORY
# ══════════════════════════════════════════════════════
with tab3:
    st.markdown("### Query History")
    st.markdown("All questions asked during this session.")

    if st.session_state.query_history:
        df_history = pd.DataFrame(st.session_state.query_history)
        st.dataframe(df_history, use_container_width=True)

        if st.button("Clear History"):
            st.session_state.query_history = []
            st.rerun()
    else:
        st.info("No queries yet. Go to the AI Assistant tab and ask a question.")

# ── Footer ────────────────────────────────────────────
st.divider()
st.markdown(
    f"<center style='color: {COLORS['text_secondary']}; font-size: 12px;'>"
    "Built with Python · MySQL · Groq API · Streamlit · Plotly"
    "</center>",
    unsafe_allow_html=True
)
