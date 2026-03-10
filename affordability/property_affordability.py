import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import json
import urllib.parse

# ── URL Query Param Persistence ───────────────────────────────────────────────
# All inputs are encoded into the URL as a single compressed JSON param.
# Sharing the URL = sharing your exact scenario. Works on Streamlit Cloud.

def load_inputs() -> dict:
    """Read saved inputs from ?d= query param (base64-encoded JSON)."""
    raw = st.query_params.get("d", "")
    if raw:
        try:
            return json.loads(urllib.parse.unquote(raw))
        except Exception:
            pass
    return {}

def save_inputs(num_periods: int):
    """Encode all current widget values into the URL query param."""
    keys = [
        "property_value", "down_payment_pct", "loan_tenor",
        "variable_haircut", "rental_income", "rental_haircut",
        "cpf_you", "cpf_you_pct", "cpf_mum", "cpf_mum_pct",
        "exp_food", "exp_transport", "exp_utilities", "exp_insurance",
        "exp_childcare", "exp_lifestyle", "exp_travel", "exp_family", "exp_other",
        "existing_monthly_debt", "your_age", "num_children", "spouse_working",
    ]
    data = {k: st.session_state[k] for k in keys if k in st.session_state}
    for i in range(num_periods):
        for k in [f"you_fixed_{i}", f"you_var_{i}", f"mum_fixed_{i}", f"mum_var_{i}", f"interest_rate_{i}"]:
            if k in st.session_state:
                data[k] = st.session_state[k]
    encoded = urllib.parse.quote(json.dumps(data, separators=(",", ":")))
    st.query_params["d"] = encoded

saved = load_inputs()  # loaded once at startup

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Property Affordability Calculator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

[data-testid="stSidebar"] {
    background: #0f1923;
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] * { color: #c8d8e8 !important; }
[data-testid="stSidebar"] .stSlider > div > div > div { background: #1e7e5c !important; }
[data-testid="stSidebar"] label {
    font-size: 0.78rem !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #7a9bb5 !important;
    font-weight: 500;
}
.main .block-container { padding-top: 2rem; background: #f7f4ef; }

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem; color: #0f1923; line-height: 1.1; margin-bottom: 0.2rem;
}
.hero-sub {
    font-size: 0.9rem; color: #5a7a8a;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2rem;
}

.kpi-card {
    background: #fff; border-radius: 12px; padding: 1.4rem 1.6rem;
    border-left: 4px solid #1e7e5c; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}
.kpi-card.red   { border-left-color: #c0392b; }
.kpi-card.amber { border-left-color: #e67e22; }
.kpi-card.blue  { border-left-color: #2980b9; }
.kpi-card.purple{ border-left-color: #8e44ad; }
.kpi-label { font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:#7a9bb5; margin-bottom:0.4rem; }
.kpi-value { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#0f1923; line-height:1; }
.kpi-sub   { font-size:0.75rem; color:#aaa; margin-top:0.3rem; }

.verdict-box { border-radius:12px; padding:1rem 1.5rem; margin-bottom:1.5rem; font-size:0.95rem; font-weight:500; }
.verdict-ok   { background:#e8f8f2; color:#1a6644; border:1px solid #9fd3bc; }
.verdict-warn { background:#fef9e7; color:#7d6608; border:1px solid #f7dc6f; }
.verdict-bad  { background:#fdedec; color:#922b21; border:1px solid #f1948a; }

.section-label {
    font-size:0.72rem; text-transform:uppercase; letter-spacing:0.1em; color:#7a9bb5;
    margin:1.8rem 0 0.8rem 0; border-bottom:1px solid #dde3e8; padding-bottom:0.4rem;
}
.borrower-tag {
    display:inline-block; padding:0.15rem 0.6rem; border-radius:20px;
    font-size:0.78rem; font-weight:600; letter-spacing:0.05em; margin-bottom:0.6rem;
}
.tag-you   { background:#d4edda; color:#1a5c2e; }
.tag-mum   { background:#d6eaf8; color:#1a4a6e; }
[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    r = annual_rate / 12
    if r == 0 or months == 0:
        return principal / max(months, 1)
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)

def fmt_sgd(v: float, decimals: int = 0) -> str:
    return f"SGD {v:,.{decimals}f}"

def recognised_monthly_income(fixed_pa: float, var_pct: float, var_haircut: float) -> float:
    """Bank-recognised monthly income after variable haircut."""
    return fixed_pa / 12 + (fixed_pa * var_pct / 100 / 12) * var_haircut / 100

def get_period_idx(year_1based: int, num_periods: int) -> int:
    return min((year_1based - 1) // 5, num_periods - 1)

# ── Singapore Personal Income Tax Engine ─────────────────────────────────────
# YA2024 resident individual tax brackets
SG_TAX_BRACKETS = [
    (20_000,       0.000),
    (10_000,       0.020),
    (10_000,       0.035),
    (40_000,       0.070),
    (40_000,       0.115),
    (40_000,       0.150),
    (40_000,       0.180),
    (40_000,       0.190),
    (40_000,       0.195),
    (40_000,       0.200),
    (float("inf"), 0.220),
]

def sg_income_tax(chargeable_income: float) -> float:
    tax, remaining = 0.0, max(chargeable_income, 0)
    for band, rate in SG_TAX_BRACKETS:
        if remaining <= 0:
            break
        taxable = min(remaining, band)
        tax += taxable * rate
        remaining -= taxable
    return tax

def sg_cpf_employee(gross_monthly: float, age: int = 35) -> float:
    """Annual employee CPF on ordinary wages (OW ceiling SGD 6,800/mo)."""
    ow = min(gross_monthly, 6_800)
    rate = 0.20 if age <= 55 else (0.13 if age <= 60 else (0.075 if age <= 65 else 0.05))
    return ow * 12 * rate

def compute_sg_tax(fixed_pa: float, var_pa: float, age: int,
                   num_children: int, spouse_working: bool) -> dict:
    """
    Full SG personal income tax for a male resident taxpayer.
    Reliefs applied: Earned Income, CPF, Spouse (if applicable),
    Qualifying Child Relief, NSman (self).
    PTR spread over 5 years as annual rebate approximation.
    """
    gross      = fixed_pa + var_pa
    cpf_ee     = sg_cpf_employee(gross / 12, age)

    reliefs = {}
    # Earned Income Relief
    reliefs["Earned Income Relief"] = (1_000 if age < 55 else 6_000 if age < 60 else 8_000)
    # CPF Relief (employee contribution, capped)
    reliefs["CPF Relief"] = min(cpf_ee, 37_740)
    # Spouse Relief (claim if spouse not working / income < SGD 4k)
    if not spouse_working:
        reliefs["Spouse Relief"] = 2_000
    # Qualifying Child Relief — SGD 4,000 per child
    if num_children > 0:
        reliefs["Qualifying Child Relief"] = num_children * 4_000
    # NSman (self) relief
    reliefs["NSman (Self) Relief"] = 1_500

    total_relief    = sum(reliefs.values())
    chargeable      = max(gross - total_relief, 0)
    tax_before      = sg_income_tax(chargeable)

    # Parenthood Tax Rebate — SGD 5k / 10k / 20k per child (spread ~5 yrs)
    ptr_map  = {1: 5_000, 2: 10_000}
    ptr_total = sum(ptr_map.get(c, 20_000) for c in range(1, num_children + 1))
    ptr_annual = ptr_total / 5

    tax_payable = max(tax_before - ptr_annual, 0)

    return {
        "Gross Income":      gross,
        "CPF (Employee)":    cpf_ee,
        "Total Reliefs":     total_relief,
        "Chargeable Income": chargeable,
        "Tax Before Rebate": tax_before,
        "PTR (annualised)":  ptr_annual,
        "Tax Payable":       tax_payable,
        "Effective Rate (%)": tax_payable / gross * 100 if gross > 0 else 0,
        "reliefs_detail":    reliefs,
    }

def amortisation_with_dynamic_income(
    principal, rate_periods, tenor_years,
    periods_you, periods_mum, var_haircut,
    cpf_you, cpf_pct_you, cpf_mum, cpf_pct_mum,
    total_expenses, existing_debt, rental_monthly_recognised,
    your_age, num_children, spouse_working,
):
    """
    rate_periods: list of annual interest rates (one per 5-yr period).
    Uses a variable-rate amortisation: recalculates payment at each rate change.
    Surplus uses real net take-home (gross - tax - CPF).
    TDSR uses bank-recognised income (variable haircut applied).
    """
    months = tenor_years * 12
    cpf_monthly = (cpf_you * cpf_pct_you / 100) + (cpf_mum * cpf_pct_mum / 100)
    n_periods_you = len(periods_you)
    n_periods_mum = len(periods_mum)
    n_rate_periods = len(rate_periods)

    rows = []
    balance = principal
    for m in range(1, months + 1):
        yr = (m - 1) // 12 + 1
        period_idx = get_period_idx(yr, n_rate_periods)
        r_annual = rate_periods[period_idx] / 100
        r_monthly = r_annual / 12

        if m == 1 or (m - 1) % 60 == 0:
            remaining_months = months - m + 1
            if r_monthly == 0:
                pmt = balance / remaining_months
            else:
                pmt = balance * r_monthly * (1 + r_monthly) ** remaining_months / \
                      ((1 + r_monthly) ** remaining_months - 1)

        interest = balance * r_monthly
        principal_paid = pmt - interest
        balance = max(balance - principal_paid, 0)
        cash_pmt = max(pmt - cpf_monthly, 0)

        p_you = periods_you[get_period_idx(yr, n_periods_you)]
        p_mum = periods_mum[get_period_idx(yr, n_periods_mum)]

        # TDSR: bank-recognised income with variable haircut
        rec_you = recognised_monthly_income(p_you["fixed"], p_you["var_pct"], var_haircut)
        rec_mum = recognised_monthly_income(p_mum["fixed"], p_mum["var_pct"], var_haircut)
        total_rec = rec_you + rec_mum + rental_monthly_recognised
        tdsr = (pmt + existing_debt) / total_rec * 100 if total_rec > 0 else 999

        # Surplus: real net take-home (gross - tax - CPF, no variable haircut)
        age_now = your_age + (yr - 1)
        _, net_you = gross_and_net_monthly(p_you, age_now, num_children, spouse_working)
        _, net_mum = gross_and_net_monthly(p_mum, age_now + 25, 0, True)
        surplus = net_you + net_mum - cash_pmt - total_expenses - existing_debt

        rows.append({
            "Month": m, "Year": yr,
            "Rate (%)": r_annual * 100,
            "Payment": pmt, "Principal": principal_paid,
            "Interest": interest, "Balance": balance,
            "Rec. Income You": rec_you, "Rec. Income Mum": rec_mum,
            "Joint Recognised": total_rec,
            "TDSR (%)": tdsr,
            "Cash Mortgage": cash_pmt,
            "Est. Surplus": surplus,
        })
    return pd.DataFrame(rows)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 Inputs")

    st.markdown("### Loan Parameters")
    property_value   = st.number_input("Property Value (SGD)", value=saved.get("property_value", 4_500_000), step=50_000, format="%d", key="property_value")
    down_payment_pct = st.slider("Down Payment (%)", 5, 75, saved.get("down_payment_pct", 25),
                                  help="MAS: min 25% for 2nd property (5% cash + 20% CPF/cash)", key="down_payment_pct")
    loan_tenor       = st.slider("Loan Tenor (years)", 5, 35, saved.get("loan_tenor", 22), key="loan_tenor")
    st.caption("💡 Interest rates are set per 5-year period in the schedule below.")

    st.markdown("### Variable Income")
    variable_haircut = st.slider("Variable Income Recognised (%)", 0, 100, saved.get("variable_haircut", 70),
                                  help="Applied to both borrowers; ~70% is standard in SG banks", key="variable_haircut")

    st.markdown("### Rental Income")
    rental_income  = st.number_input("Rental Income p.a. (SGD)", value=saved.get("rental_income", 0), step=1_000, format="%d", key="rental_income")
    rental_haircut = st.slider("Rental Credit (%)", 0, 100, saved.get("rental_haircut", 70), key="rental_haircut")

    st.markdown("### CPF — You")
    cpf_you     = st.number_input("Your Monthly CPF OA (SGD)", value=saved.get("cpf_you", 2_200), step=100, format="%d", key="cpf_you")
    cpf_pct_you = st.slider("Your CPF for Mortgage (%)", 0, 100, saved.get("cpf_you_pct", 100), key="cpf_you_pct")

    st.markdown("### CPF — Mum")
    cpf_mum     = st.number_input("Mum's Monthly CPF OA (SGD)", value=saved.get("cpf_mum", 600), step=100, format="%d", key="cpf_mum")
    cpf_pct_mum = st.slider("Mum's CPF for Mortgage (%)", 0, 100, saved.get("cpf_mum_pct", 60), key="cpf_mum_pct")

    st.markdown("### Monthly Expenses")
    exp_food      = st.number_input("Food & Groceries",         value=saved.get("exp_food",      3_000), step=100, format="%d", key="exp_food")
    exp_transport = st.number_input("Transport / Car",           value=saved.get("exp_transport", 3_500), step=100, format="%d", key="exp_transport")
    exp_utilities = st.number_input("Utilities & Telco",         value=saved.get("exp_utilities", 1_300), step=50,  format="%d", key="exp_utilities")
    exp_insurance = st.number_input("Insurance Premiums",        value=saved.get("exp_insurance", 3_000), step=100, format="%d", key="exp_insurance")
    exp_childcare = st.number_input("Childcare / Education",     value=saved.get("exp_childcare", 2_000), step=100, format="%d", key="exp_childcare")
    exp_lifestyle = st.number_input("Lifestyle & Entertainment", value=saved.get("exp_lifestyle", 1_000), step=100, format="%d", key="exp_lifestyle")
    exp_travel    = st.number_input("Travel (monthly amort.)",   value=saved.get("exp_travel",    1_000), step=100, format="%d", key="exp_travel")
    exp_family    = st.number_input("Family Support",            value=saved.get("exp_family",    1_000), step=100, format="%d", key="exp_family")
    exp_other     = st.number_input("Other / Misc",              value=saved.get("exp_other",     4_000), step=100, format="%d", key="exp_other")

    st.markdown("### Existing Debt")
    existing_monthly_debt = st.number_input("Other Monthly Debt (SGD)", value=saved.get("existing_monthly_debt", 0), step=100, format="%d", key="existing_monthly_debt")

    st.markdown("### Your Tax Profile")
    your_age       = st.slider("Your Age", 22, 65, saved.get("your_age", 33), key="your_age")
    num_children   = st.slider("Number of Children", 0, 5, saved.get("num_children", 2), key="num_children")
    spouse_working = st.checkbox("Spouse is working / income > SGD 4k p.a.",
                                  value=saved.get("spouse_working", True), key="spouse_working",
                                  help="Untick to claim Spouse Relief of SGD 2,000")

    st.markdown("---")
    if st.button("🔗 Save & Get Shareable Link", use_container_width=True):
        save_inputs(math.ceil(st.session_state["loan_tenor"] / 5))
        st.success("✅ URL updated! Copy the browser address bar to share this exact scenario.")
        st.caption("The link encodes all your inputs — anyone with it loads your scenario instantly.")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Property Affordability</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Joint Purchase · You & Mum · Singapore</div>', unsafe_allow_html=True)

# ── SALARY SCHEDULE EDITOR ────────────────────────────────────────────────────
num_periods    = math.ceil(loan_tenor / 5)
period_labels  = []
for i in range(num_periods):
    s = i * 5 + 1
    e = min((i + 1) * 5, loan_tenor)
    period_labels.append(f"Years {s}–{e}")

st.markdown('<div class="section-label">Income & Rate Schedule — Edit Each 5-Year Period</div>', unsafe_allow_html=True)
st.caption("Adjust each borrower's salary and the expected interest rate per 5-year window. Mortgage payment recalculates at each rate change.")

periods_you  = []
periods_mum  = []
rate_periods = []

tabs = st.tabs(period_labels)
for i, tab in enumerate(tabs):
    with tab:
        # ── Interest rate row ──
        default_rates = [1.6, 1.8, 2.4, 2.6, 2.6]
        default_rate  = default_rates[i] if i < len(default_rates) else 3.5
        rate_i = st.slider(
            "🏦 Interest Rate (% p.a.)",
            min_value=1.0, max_value=7.0,
            value=float(saved.get(f"interest_rate_{i}", default_rate)),
            step=0.05, key=f"interest_rate_{i}",
            help=f"Rate applied for {period_labels[i]}",
        )
        rate_periods.append(rate_i)

        st.markdown("---")
        col_you, col_mum = st.columns(2)

        # Per-period defaults from last_inputs.json
        you_fixed_defaults = [192_000, 200_000, 220_000, 240_000, 260_000]
        you_var_defaults   = [60,      55,      55,      55,      55]
        mum_fixed_defaults = [180_000, 120_000,  60_000,       0,      0]
        mum_var_defaults   = [0,       0,        0,            0,     10]

        with col_you:
            st.markdown('<span class="borrower-tag tag-you">👤 You</span>', unsafe_allow_html=True)
            f_you = st.number_input("Fixed Salary p.a. (SGD)",
                                     value=saved.get(f"you_fixed_{i}", you_fixed_defaults[i] if i < len(you_fixed_defaults) else 180_000),
                                     step=5_000, format="%d", key=f"you_fixed_{i}")
            v_you = st.slider("Bonus (%)", 0, 150,
                               saved.get(f"you_var_{i}", you_var_defaults[i] if i < len(you_var_defaults) else 20),
                               key=f"you_var_{i}", help="% of fixed salary")
            periods_you.append({"fixed": f_you, "var_pct": v_you})

        with col_mum:
            st.markdown('<span class="borrower-tag tag-mum">👩 Mum</span>', unsafe_allow_html=True)
            f_mum = st.number_input("Fixed Salary p.a. (SGD)",
                                     value=saved.get(f"mum_fixed_{i}", mum_fixed_defaults[i] if i < len(mum_fixed_defaults) else 80_000),
                                     step=5_000, format="%d", key=f"mum_fixed_{i}")
            v_mum = st.slider("Bonus (%)", 0, 150,
                               saved.get(f"mum_var_{i}", mum_var_defaults[i] if i < len(mum_var_defaults) else 0),
                               key=f"mum_var_{i}", help="% of fixed salary")
            periods_mum.append({"fixed": f_mum, "var_pct": v_mum})

# ── CORE CALCULATIONS ─────────────────────────────────────────────────────────
down_payment   = property_value * down_payment_pct / 100
loan_amount    = property_value - down_payment
months_total   = loan_tenor * 12
interest_rate  = rate_periods[0]
mthly_pmt_yr1  = monthly_payment(loan_amount, interest_rate / 100, months_total)
cpf_monthly    = (cpf_you * cpf_pct_you / 100) + (cpf_mum * cpf_pct_mum / 100)
cash_mortgage  = max(mthly_pmt_yr1 - cpf_monthly, 0)
total_expenses = (exp_food + exp_transport + exp_utilities + exp_insurance +
                  exp_childcare + exp_lifestyle + exp_travel + exp_family + exp_other)
rental_monthly_recognised = (rental_income / 12) * rental_haircut / 100

# ── Tax calculation (your income only — mum handled separately below) ─────────
def gross_and_net_monthly(period: dict, age: int, n_children: int, sp_working: bool) -> tuple:
    """Returns (gross_monthly, net_take_home_monthly) using real SG tax."""
    fixed_pa = period["fixed"]
    var_pa   = fixed_pa * period["var_pct"] / 100
    tx       = compute_sg_tax(fixed_pa, var_pa, age, n_children, sp_working)
    cpf_ee   = tx["CPF (Employee)"]
    tax_pa   = tx["Tax Payable"]
    net_pa   = fixed_pa + var_pa - cpf_ee - tax_pa
    return (fixed_pa + var_pa) / 12, net_pa / 12

# Year-1 tax details (your income only for tax panel)
yr1_fixed_you = periods_you[0]["fixed"]
yr1_var_you   = yr1_fixed_you * periods_you[0]["var_pct"] / 100
tax_you_yr1   = compute_sg_tax(yr1_fixed_you, yr1_var_you, your_age, num_children, spouse_working)

# Mum's tax (simplified — single, no children claimed)
yr1_fixed_mum = periods_mum[0]["fixed"]
yr1_var_mum   = yr1_fixed_mum * periods_mum[0]["var_pct"] / 100
tax_mum_yr1   = compute_sg_tax(yr1_fixed_mum, yr1_var_mum, your_age + 25, 0, True)

# Year-1 net take-home (both borrowers)
_, net_you_mo_yr1 = gross_and_net_monthly(periods_you[0], your_age, num_children, spouse_working)
_, net_mum_mo_yr1 = gross_and_net_monthly(periods_mum[0], your_age + 25, 0, True)
net_home_yr1 = net_you_mo_yr1 + net_mum_mo_yr1

# TDSR still uses bank-recognised income (with variable haircut)
rec_you_yr1   = recognised_monthly_income(yr1_fixed_you, periods_you[0]["var_pct"], variable_haircut)
rec_mum_yr1   = recognised_monthly_income(yr1_fixed_mum, periods_mum[0]["var_pct"], variable_haircut)
total_rec_yr1 = rec_you_yr1 + rec_mum_yr1 + rental_monthly_recognised
tdsr_yr1      = (mthly_pmt_yr1 + existing_monthly_debt) / total_rec_yr1 * 100 if total_rec_yr1 > 0 else 999

# Surplus uses real net take-home (no haircut)
surplus_yr1 = net_home_yr1 - cash_mortgage - total_expenses - existing_monthly_debt

# Full schedule (variable rate, real net take-home)
df_amort = amortisation_with_dynamic_income(
    loan_amount, rate_periods, loan_tenor,
    periods_you, periods_mum, variable_haircut,
    cpf_you, cpf_pct_you, cpf_mum, cpf_pct_mum,
    total_expenses, existing_monthly_debt, rental_monthly_recognised,
    your_age, num_children, spouse_working,
)
total_interest = df_amort["Interest"].sum()
total_cost     = loan_amount + total_interest + down_payment

# Per-year summary for charts
years = list(range(1, loan_tenor + 1))
rec_you_by_yr  = [recognised_monthly_income(periods_you[get_period_idx(y, num_periods)]["fixed"],
                                              periods_you[get_period_idx(y, num_periods)]["var_pct"],
                                              variable_haircut) for y in years]
rec_mum_by_yr  = [recognised_monthly_income(periods_mum[get_period_idx(y, num_periods)]["fixed"],
                                              periods_mum[get_period_idx(y, num_periods)]["var_pct"],
                                              variable_haircut) for y in years]
joint_rec_yr   = [a + b + rental_monthly_recognised for a, b in zip(rec_you_by_yr, rec_mum_by_yr)]

# Monthly payment per year (recalculated at each rate-change period)
pmt_by_yr = []
_balance = loan_amount
for y in years:
    m_start = (y - 1) * 12 + 1
    r_idx   = get_period_idx(y, len(rate_periods))
    r_m     = rate_periods[r_idx] / 100 / 12
    remaining = months_total - m_start + 1
    if r_m == 0:
        _pmt = _balance / remaining if remaining > 0 else 0
    else:
        _pmt = _balance * r_m * (1 + r_m) ** remaining / ((1 + r_m) ** remaining - 1) if remaining > 0 else 0
    pmt_by_yr.append(_pmt)
    # advance balance by 12 months at this rate
    for _ in range(12):
        if _balance <= 0:
            break
        _interest = _balance * r_m
        _balance  = max(_balance - (_pmt - _interest), 0)

tdsr_by_yr = [(pmt_by_yr[i] + existing_monthly_debt) / joint_rec_yr[i] * 100
              if joint_rec_yr[i] > 0 else 999 for i in range(len(years))]
cash_mortgage_by_yr = [max(p - cpf_monthly, 0) for p in pmt_by_yr]
surplus_by_yr = []
for i, y in enumerate(years):
    age_now = your_age + (y - 1)
    _, net_you = gross_and_net_monthly(periods_you[get_period_idx(y, num_periods)], age_now, num_children, spouse_working)
    _, net_mum = gross_and_net_monthly(periods_mum[get_period_idx(y, num_periods)], age_now + 25, 0, True)
    surplus_by_yr.append(net_you + net_mum - cash_mortgage_by_yr[i] - total_expenses - existing_monthly_debt)
rate_by_yr = [rate_periods[get_period_idx(y, len(rate_periods))] for y in years]

# ── VERDICT ───────────────────────────────────────────────────────────────────
months_above_55 = int((df_amort["TDSR (%)"] > 55).sum())
if tdsr_yr1 <= 40 and months_above_55 == 0:
    vc = "verdict-ok";   vi = "✅"
    vm = f"Year-1 TDSR is {tdsr_yr1:.1f}% — well within MAS 55% limit. Joint income is comfortably sufficient."
elif tdsr_yr1 <= 55:
    vc = "verdict-warn"; vi = "⚠️"
    vm = f"Year-1 TDSR is {tdsr_yr1:.1f}% — within MAS 55% limit but stretched."
    if months_above_55:
        vm += f" ⚡ TDSR breaches 55% in {months_above_55} month(s) based on future income projections."
else:
    vc = "verdict-bad";  vi = "🚫"
    vm = f"Year-1 TDSR is {tdsr_yr1:.1f}% — EXCEEDS MAS 55% limit. Loan likely not approvable as structured."

st.markdown(f'<div class="verdict-box {vc}">{vi} {vm}</div>', unsafe_allow_html=True)

# ── KPI ROW ───────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.markdown(f"""<div class="kpi-card">
  <div class="kpi-label">Monthly Mortgage (Yr 1)</div>
  <div class="kpi-value">{fmt_sgd(mthly_pmt_yr1)}</div>
  <div class="kpi-sub">Cash: {fmt_sgd(cash_mortgage)} · CPF: {fmt_sgd(cpf_monthly)} · Rate: {interest_rate:.2f}%</div>
</div>""", unsafe_allow_html=True)

tdsr_color = "red" if tdsr_yr1 > 55 else "amber" if tdsr_yr1 > 40 else ""
kpi2.markdown(f"""<div class="kpi-card {tdsr_color}">
  <div class="kpi-label">TDSR (Year 1)</div>
  <div class="kpi-value">{tdsr_yr1:.1f}%</div>
  <div class="kpi-sub">Joint income · MAS limit 55%</div>
</div>""", unsafe_allow_html=True)

surp_color = "red" if surplus_yr1 < 0 else "blue"
kpi3.markdown(f"""<div class="kpi-card {surp_color}">
  <div class="kpi-label">Monthly Surplus (Yr 1)</div>
  <div class="kpi-value">{fmt_sgd(surplus_yr1)}</div>
  <div class="kpi-sub">After tax, CPF, mortgage & expenses</div>
</div>""", unsafe_allow_html=True)

kpi4.markdown(f"""<div class="kpi-card purple">
  <div class="kpi-label">Total Interest</div>
  <div class="kpi-value">{fmt_sgd(total_interest)}</div>
  <div class="kpi-sub">Total outlay: {fmt_sgd(total_cost)}</div>
</div>""", unsafe_allow_html=True)

# ── TAX PANEL ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Your Singapore Income Tax Estimate (YA2024 Basis)</div>', unsafe_allow_html=True)

tax_col1, tax_col2, tax_col3 = st.columns(3)

with tax_col1:
    st.markdown("**Your Income & Tax (Year 1)**")
    st.write(f"Gross Income: **{fmt_sgd(tax_you_yr1['Gross Income'])}**")
    st.write(f"CPF (Employee): **{fmt_sgd(tax_you_yr1['CPF (Employee)'])}**")
    st.write(f"Total Reliefs: **{fmt_sgd(tax_you_yr1['Total Reliefs'])}**")
    st.write(f"Chargeable Income: **{fmt_sgd(tax_you_yr1['Chargeable Income'])}**")
    st.write(f"Tax Before Rebate: **{fmt_sgd(tax_you_yr1['Tax Before Rebate'])}**")
    st.write(f"PTR (annualised): **({fmt_sgd(tax_you_yr1['PTR (annualised)'])})**")
    st.markdown(f"**Tax Payable: {fmt_sgd(tax_you_yr1['Tax Payable'])}** *(Eff. {tax_you_yr1['Effective Rate (%)']:.1f}%)*")

with tax_col2:
    st.markdown("**Your Relief Breakdown**")
    for name, amt in tax_you_yr1["reliefs_detail"].items():
        st.write(f"{name}: **{fmt_sgd(amt)}**")
    st.markdown("---")
    st.caption("Based on: married male resident, SG-sourced employment income. "
               "CPF Relief = employee contribution. PTR spread ~5 years. "
               "Does not include SRS, course fees, or other optional reliefs.")

with tax_col3:
    # Tax projection across all periods
    st.markdown("**Your Tax by Income Period**")
    tax_rows = []
    for i, p in enumerate(periods_you):
        var_pa = p["fixed"] * p["var_pct"] / 100
        age_i  = your_age + i * 5
        tx     = compute_sg_tax(p["fixed"], var_pa, age_i, num_children, spouse_working)
        tax_rows.append({
            "Period":           period_labels[i],
            "Gross p.a.":       f"SGD {tx['Gross Income']:,.0f}",
            "Tax Payable":      f"SGD {tx['Tax Payable']:,.0f}",
            "Effective Rate":   f"{tx['Effective Rate (%)']:.1f}%",
            "Monthly Tax":      f"SGD {tx['Tax Payable']/12:,.0f}",
        })
    st.dataframe(pd.DataFrame(tax_rows), use_container_width=True, hide_index=True)

    # Quick bar chart
    tax_vals  = []
    net_vals  = []
    cpf_vals  = []
    lbl_vals  = []
    for i, p in enumerate(periods_you):
        var_pa = p["fixed"] * p["var_pct"] / 100
        age_i  = your_age + i * 5
        tx     = compute_sg_tax(p["fixed"], var_pa, age_i, num_children, spouse_working)
        tax_vals.append(tx["Tax Payable"] / 12)
        cpf_vals.append(tx["CPF (Employee)"] / 12)
        net_vals.append((tx["Gross Income"] - tx["Tax Payable"] - tx["CPF (Employee)"]) / 12)
        lbl_vals.append(period_labels[i])

    fig_tax = go.Figure()
    fig_tax.add_trace(go.Bar(name="Net Take-Home", x=lbl_vals, y=net_vals, marker_color="#1e7e5c"))
    fig_tax.add_trace(go.Bar(name="CPF",           x=lbl_vals, y=cpf_vals, marker_color="#2980b9"))
    fig_tax.add_trace(go.Bar(name="Tax",           x=lbl_vals, y=tax_vals, marker_color="#c0392b"))
    fig_tax.update_layout(
        barmode="stack", height=220,
        paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
        font=dict(family="DM Sans", color="#0f1923", size=11),
        legend=dict(orientation="h", y=-0.35),
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(tickformat=",.0f", gridcolor="#e0dbd2"),
        title=dict(text="Your Monthly Gross Breakdown by Period", font=dict(size=12)),
    )
    st.plotly_chart(fig_tax, use_container_width=True)

# ── INCOME PROGRESSION CHART ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Joint Income Progression vs Mortgage Burden</div>', unsafe_allow_html=True)

fig_inc = make_subplots(specs=[[{"secondary_y": True}]])
fig_inc.add_trace(go.Bar(x=years, y=rec_you_by_yr, name="You (recognised)",
                          marker_color="#1e7e5c", opacity=0.9), secondary_y=False)
fig_inc.add_trace(go.Bar(x=years, y=rec_mum_by_yr, name="Mum (recognised)",
                          marker_color="#2980b9", opacity=0.9), secondary_y=False)
fig_inc.add_trace(go.Scatter(x=years, y=pmt_by_yr, name="Monthly Mortgage",
                              line=dict(color="#c0392b", width=2.5, dash="dash"),
                              mode="lines"), secondary_y=False)
fig_inc.add_trace(go.Scatter(x=years, y=tdsr_by_yr, name="TDSR (%)",
                              line=dict(color="#e67e22", width=2.5),
                              mode="lines+markers", marker=dict(size=5)), secondary_y=True)
fig_inc.add_hline(y=55, line=dict(color="#c0392b", dash="dot", width=1.2),
                  annotation_text="55% TDSR Limit", secondary_y=True,
                  annotation_position="top right")
# Add 5-year boundary lines
for i in range(1, num_periods):
    fig_inc.add_vline(x=i * 5 + 0.5, line=dict(color="#aaa", dash="dot", width=1))
fig_inc.update_layout(
    barmode="stack", height=360,
    paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
    font=dict(family="DM Sans", color="#0f1923"),
    legend=dict(orientation="h", y=-0.22),
    margin=dict(l=0, r=0, t=10, b=10),
    xaxis=dict(title="Year of Loan", gridcolor="#e0dbd2", dtick=1),
)
fig_inc.update_yaxes(title_text="Monthly SGD", secondary_y=False,
                      tickformat=",.0f", gridcolor="#e0dbd2")
fig_inc.update_yaxes(title_text="TDSR (%)", secondary_y=True,
                      tickformat=".0f", ticksuffix="%", showgrid=False)
st.plotly_chart(fig_inc, use_container_width=True)

# ── EXPENSES & CASHFLOW ANALYTICS ────────────────────────────────────────────
st.markdown('<div class="section-label">Monthly Cashflow Breakdown</div>', unsafe_allow_html=True)

# ── Build per-year cashflow table ─────────────────────────────────────────────
cf_rows = []
for i, y in enumerate(years):
    age_now  = your_age + (y - 1)
    p_you    = periods_you[get_period_idx(y, num_periods)]
    p_mum    = periods_mum[get_period_idx(y, num_periods)]
    tx_you   = compute_sg_tax(p_you["fixed"], p_you["fixed"] * p_you["var_pct"] / 100,
                               age_now, num_children, spouse_working)
    tx_mum   = compute_sg_tax(p_mum["fixed"], p_mum["fixed"] * p_mum["var_pct"] / 100,
                               age_now + 25, 0, True)
    gross_you_mo = tx_you["Gross Income"] / 12
    gross_mum_mo = tx_mum["Gross Income"] / 12
    tax_you_mo   = tx_you["Tax Payable"] / 12
    tax_mum_mo   = tx_mum["Tax Payable"] / 12
    cpf_you_mo   = tx_you["CPF (Employee)"] / 12
    cpf_mum_mo   = tx_mum["CPF (Employee)"] / 12
    net_you_mo   = gross_you_mo - tax_you_mo - cpf_you_mo
    net_mum_mo   = gross_mum_mo - tax_mum_mo - cpf_mum_mo
    net_total    = net_you_mo + net_mum_mo
    cash_mtg     = cash_mortgage_by_yr[i]
    surplus      = surplus_by_yr[i]
    cf_rows.append({
        "Year":        y,
        "Gross (Joint)":   gross_you_mo + gross_mum_mo,
        "Tax (Joint)":     tax_you_mo + tax_mum_mo,
        "CPF (Joint)":     cpf_you_mo + cpf_mum_mo,
        "Net Take-Home":   net_total,
        "Cash Mortgage":   cash_mtg,
        "Mortgage %":      cash_mtg / net_total * 100 if net_total > 0 else 0,
        "Food & Groceries":     exp_food,
        "Transport":            exp_transport,
        "Utilities & Telco":    exp_utilities,
        "Insurance":            exp_insurance,
        "Childcare / Education":exp_childcare,
        "Lifestyle":            exp_lifestyle,
        "Travel":               exp_travel,
        "Family Support":       exp_family,
        "Other / Misc":         exp_other,
        "Other Debt":      existing_monthly_debt,
        "Total Expenses":  total_expenses + existing_monthly_debt,
        "Surplus":         surplus,
        "Surplus %":       surplus / net_total * 100 if net_total > 0 else 0,
    })
df_cf = pd.DataFrame(cf_rows)

# ─── Row 1: Expense donut (Year 1) + Stacked cashflow by year ──────────────
cf_left, cf_right = st.columns([1, 2])

with cf_left:
    # Donut: full gross income composition for Year 1 (Tax + CPF + all spending + surplus)
    yr1 = cf_rows[0]
    donut_labels = [
        "Income Tax",
        "CPF (Employee)",
        "Cash Mortgage",
        "Food & Groceries", "Transport", "Utilities & Telco",
        "Insurance", "Childcare / Education", "Lifestyle",
        "Travel", "Family Support", "Other / Misc", "Other Debt",
        "Surplus",
    ]
    donut_values = [
        yr1["Tax (Joint)"],
        yr1["CPF (Joint)"],
        yr1["Cash Mortgage"],
        exp_food, exp_transport, exp_utilities,
        exp_insurance, exp_childcare, exp_lifestyle,
        exp_travel, exp_family, exp_other, existing_monthly_debt,
        max(yr1["Surplus"], 0),
    ]
    donut_colors = [
        "#922b21",   # Tax — dark red
        "#1a5276",   # CPF — dark blue
        "#c0392b",   # Mortgage — red
        "#1e7e5c", "#2980b9", "#8e44ad",
        "#e67e22", "#16a085", "#d35400",
        "#2c3e50", "#7f8c8d", "#95a5a6", "#bdc3c7",
        "#27ae60",   # Surplus — green
    ]
    # Filter zero values
    filtered = [(l, v, c) for l, v, c in zip(donut_labels, donut_values, donut_colors) if v > 0]
    f_labels, f_values, f_colors = zip(*filtered) if filtered else ([], [], [])

    fig_donut = go.Figure(go.Pie(
        labels=f_labels, values=f_values,
        hole=0.52,
        marker=dict(colors=f_colors, line=dict(color="#f7f4ef", width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>SGD %{value:,.0f}/mo<br>%{percent}<extra></extra>",
        sort=False,
    ))
    gross_yr1 = yr1["Gross (Joint)"]
    fig_donut.update_layout(
        height=360,
        paper_bgcolor="#f7f4ef",
        font=dict(family="DM Sans", color="#0f1923", size=11),
        title=dict(text="Year 1 Gross Income Allocation", font=dict(size=12)),
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=10)),
        margin=dict(l=0, r=130, t=40, b=0),
        annotations=[dict(
            text=f"<b>{fmt_sgd(gross_yr1)}</b><br>gross/mo",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="#0f1923"),
            xanchor="center",
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with cf_right:
    # Stacked bars starting from gross: Tax → CPF → Mortgage → Expenses → Surplus
    fig_stack = go.Figure()

    # Gross income ceiling line
    gross_by_yr = [r["Gross (Joint)"] for r in cf_rows]
    fig_stack.add_trace(go.Scatter(
        x=years, y=gross_by_yr, name="Gross Income",
        mode="lines", line=dict(color="#0f1923", width=2, dash="dot"),
    ))

    stack_layers = [
        ("Income Tax",             [r["Tax (Joint)"]  for r in cf_rows], "#922b21"),
        ("CPF (Employee)",         [r["CPF (Joint)"]  for r in cf_rows], "#1a5276"),
        ("Cash Mortgage",          cash_mortgage_by_yr,                  "#c0392b"),
        ("Food & Groceries",       [exp_food]          * loan_tenor,     "#1e7e5c"),
        ("Transport",              [exp_transport]     * loan_tenor,     "#2980b9"),
        ("Utilities & Telco",      [exp_utilities]     * loan_tenor,     "#8e44ad"),
        ("Insurance",              [exp_insurance]     * loan_tenor,     "#e67e22"),
        ("Childcare / Education",  [exp_childcare]     * loan_tenor,     "#16a085"),
        ("Lifestyle",              [exp_lifestyle]     * loan_tenor,     "#d35400"),
        ("Travel",                 [exp_travel]        * loan_tenor,     "#2c3e50"),
        ("Family Support",         [exp_family]        * loan_tenor,     "#7f8c8d"),
        ("Other / Misc",           [exp_other]         * loan_tenor,     "#95a5a6"),
        ("Other Debt",             [existing_monthly_debt] * loan_tenor, "#bdc3c7"),
    ]

    for name, vals, color in stack_layers:
        if all(v == 0 for v in vals):
            continue
        fig_stack.add_trace(go.Bar(
            x=years, y=vals, name=name,
            marker_color=color, opacity=0.88,
        ))

    # Surplus scatter on top
    s_colors_stack = ["#c0392b" if s < 0 else "#27ae60" for s in surplus_by_yr]
    fig_stack.add_trace(go.Scatter(
        x=years, y=surplus_by_yr, name="Surplus",
        mode="lines+markers",
        line=dict(color="#27ae60", width=2.5),
        marker=dict(size=7, color=s_colors_stack, line=dict(color="#fff", width=1.5)),
    ))
    fig_stack.add_hline(y=0, line=dict(color="#c0392b", width=1, dash="dash"))

    for i in range(1, num_periods):
        fig_stack.add_vline(x=i * 5 + 0.5, line=dict(color="#aaa", dash="dot", width=1))

    fig_stack.update_layout(
        barmode="stack", height=360,
        paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
        font=dict(family="DM Sans", color="#0f1923"),
        legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
        margin=dict(l=0, r=0, t=40, b=10),
        title=dict(text="Monthly Gross-to-Surplus Waterfall by Year", font=dict(size=12)),
        xaxis=dict(title="Year of Loan", gridcolor="#e0dbd2", dtick=1),
        yaxis=dict(tickformat=",.0f", gridcolor="#e0dbd2", title="SGD / month"),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# ─── Row 2: Surplus runway chart + surplus % of take-home ─────────────────
surp_left, surp_right = st.columns(2)

with surp_left:
    # Bar chart: surplus coloured green/red, with mortgage-as-%-of-net-home line
    s_bar_colors = ["#c0392b" if s < 0 else "#1e7e5c" for s in surplus_by_yr]
    fig_surp2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig_surp2.add_trace(go.Bar(
        x=years, y=surplus_by_yr, name="Monthly Surplus",
        marker_color=s_bar_colors, opacity=0.85,
    ), secondary_y=False)
    fig_surp2.add_trace(go.Scatter(
        x=years, y=[r["Surplus %"] for r in cf_rows], name="Surplus % of Take-Home",
        mode="lines+markers", line=dict(color="#8e44ad", width=2),
        marker=dict(size=5),
    ), secondary_y=True)
    fig_surp2.add_hline(y=0, line=dict(color="#0f1923", width=1.2))
    for i in range(1, num_periods):
        fig_surp2.add_vline(x=i * 5 + 0.5, line=dict(color="#aaa", dash="dot", width=1))
    fig_surp2.update_layout(
        height=300, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
        font=dict(family="DM Sans", color="#0f1923"),
        title=dict(text="Monthly Surplus & Surplus Rate", font=dict(size=12)),
        legend=dict(orientation="h", y=-0.3),
        margin=dict(l=0, r=0, t=40, b=10),
        xaxis=dict(title="Year", gridcolor="#e0dbd2", dtick=1),
    )
    fig_surp2.update_yaxes(title_text="SGD/mo", secondary_y=False,
                            tickformat=",.0f", gridcolor="#e0dbd2")
    fig_surp2.update_yaxes(title_text="Surplus %", secondary_y=True,
                            tickformat=".0f", ticksuffix="%", showgrid=False)
    st.plotly_chart(fig_surp2, use_container_width=True)

with surp_right:
    # Mortgage burden % of net take-home over time
    mtg_pct_by_yr = [r["Mortgage %"] for r in cf_rows]
    fig_burden = go.Figure()
    fig_burden.add_trace(go.Scatter(
        x=years, y=mtg_pct_by_yr, name="Cash Mortgage % of Net",
        mode="lines+markers", fill="tozeroy",
        line=dict(color="#c0392b", width=2.5),
        fillcolor="rgba(192,57,43,0.08)",
        marker=dict(size=5),
    ))
    fig_burden.add_hline(y=30, line=dict(color="#e67e22", dash="dash", width=1.5),
                          annotation_text="30% guideline", annotation_position="top right")
    for i in range(1, num_periods):
        fig_burden.add_vline(x=i * 5 + 0.5, line=dict(color="#aaa", dash="dot", width=1))
    fig_burden.update_layout(
        height=300, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
        font=dict(family="DM Sans", color="#0f1923"),
        title=dict(text="Cash Mortgage as % of Joint Net Take-Home", font=dict(size=12)),
        margin=dict(l=0, r=0, t=40, b=10),
        xaxis=dict(title="Year", gridcolor="#e0dbd2", dtick=1),
        yaxis=dict(tickformat=".0f", ticksuffix="%", gridcolor="#e0dbd2"),
        showlegend=False,
    )
    st.plotly_chart(fig_burden, use_container_width=True)

# ─── Row 3: Year-by-year cashflow table ────────────────────────────────────
st.markdown("**Annual Cashflow Summary Table**")
disp_cols = [
    "Year", "Gross (Joint)", "Tax (Joint)", "CPF (Joint)", "Net Take-Home",
    "Cash Mortgage", "Mortgage %", "Total Expenses", "Surplus", "Surplus %",
]
df_cf_disp = df_cf[disp_cols].copy()
for c in ["Gross (Joint)", "Tax (Joint)", "CPF (Joint)", "Net Take-Home",
          "Cash Mortgage", "Total Expenses", "Surplus"]:
    df_cf_disp[c] = df_cf_disp[c].map(lambda x: f"{x:,.0f}")
for c in ["Mortgage %", "Surplus %"]:
    df_cf_disp[c] = df_cf_disp[c].map(lambda x: f"{x:.1f}%")
st.caption("All values are monthly (SGD). Tax and CPF deducted from gross to arrive at Net Take-Home. Surplus = Net Take-Home − Cash Mortgage − Total Expenses.")
st.dataframe(df_cf_disp, use_container_width=True, hide_index=True)

# ── AMORTISATION ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Loan Amortisation</div>', unsafe_allow_html=True)
df_yr = df_amort.groupby("Year").agg(
    Principal=("Principal", "sum"),
    Interest=("Interest", "sum"),
    Balance=("Balance", "last"),
).reset_index()
fig_am = make_subplots(specs=[[{"secondary_y": True}]])
fig_am.add_trace(go.Bar(x=df_yr["Year"], y=df_yr["Principal"],
                         name="Principal", marker_color="#1e7e5c"), secondary_y=False)
fig_am.add_trace(go.Bar(x=df_yr["Year"], y=df_yr["Interest"],
                         name="Interest", marker_color="#e8c99a"), secondary_y=False)
fig_am.add_trace(go.Scatter(x=df_yr["Year"], y=df_yr["Balance"],
                             name="Outstanding Balance",
                             line=dict(color="#c0392b", width=2.5), mode="lines"), secondary_y=True)
fig_am.update_layout(barmode="stack", height=300,
                      paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                      font=dict(family="DM Sans", color="#0f1923"),
                      legend=dict(orientation="h", y=-0.3),
                      margin=dict(l=0, r=0, t=10, b=10))
fig_am.update_yaxes(title_text="Annual Payment (SGD)", secondary_y=False,
                     tickformat=",.0f", gridcolor="#e0dbd2")
fig_am.update_yaxes(title_text="Balance (SGD)", secondary_y=True,
                     tickformat=",.0f", showgrid=False)
st.plotly_chart(fig_am, use_container_width=True)

# ── SENSITIVITY ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Sensitivity Analysis</div>', unsafe_allow_html=True)
col_s1, col_s2 = st.columns(2)

with col_s1:
    rates  = np.arange(1.5, 6.1, 0.5)
    tenors = [15, 20, 25, 30, 35]
    heat_data = pd.DataFrame(
        [[monthly_payment(loan_amount, r / 100, t * 12) for r in rates] for t in tenors],
        index=[f"{t}Y" for t in tenors],
        columns=[f"{r:.1f}%" for r in rates],
    )
    fig_heat = go.Figure(go.Heatmap(
        z=heat_data.values, x=heat_data.columns, y=heat_data.index,
        colorscale=[[0, "#e8f8f2"], [0.5, "#f7dc6f"], [1, "#c0392b"]],
        text=[[f"SGD {v:,.0f}" for v in row] for row in heat_data.values],
        texttemplate="%{text}", textfont=dict(size=10), showscale=False,
    ))
    fig_heat.update_layout(height=280, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                            font=dict(family="DM Sans", color="#0f1923"),
                            title=dict(text="Monthly Payment: Rate × Tenor", font=dict(size=13)),
                            margin=dict(l=0, r=0, t=40, b=0),
                            xaxis_title="Interest Rate", yaxis_title="Tenor")
    st.plotly_chart(fig_heat, use_container_width=True)

with col_s2:
    pvs = np.arange(1_000_000, 5_500_000, 250_000)
    tdsrs_sens = [
        (monthly_payment(pv * (1 - down_payment_pct / 100), interest_rate / 100, months_total) + existing_monthly_debt)
        / total_rec_yr1 * 100 for pv in pvs
    ]
    fig_tdsr = go.Figure()
    fig_tdsr.add_trace(go.Scatter(x=pvs, y=tdsrs_sens, mode="lines",
                                   line=dict(color="#1e7e5c", width=2.5),
                                   fill="tozeroy", fillcolor="rgba(30,126,92,0.1)"))
    fig_tdsr.add_hline(y=55, line=dict(color="#c0392b", dash="dash", width=1.5),
                        annotation_text="MAS 55% Limit", annotation_position="top right")
    fig_tdsr.add_vline(x=property_value, line=dict(color="#2980b9", dash="dot", width=1.5),
                        annotation_text="Current", annotation_position="top left")
    fig_tdsr.update_layout(height=280, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                            font=dict(family="DM Sans", color="#0f1923"),
                            title=dict(text="TDSR vs Property Value (Yr-1 Joint Income)", font=dict(size=13)),
                            margin=dict(l=0, r=0, t=40, b=0),
                            xaxis=dict(tickformat=",.0f", gridcolor="#e0dbd2"),
                            yaxis=dict(tickformat=".0f", ticksuffix="%", gridcolor="#e0dbd2"),
                            showlegend=False)
    st.plotly_chart(fig_tdsr, use_container_width=True)

# ── MONTHLY TABLE ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Monthly Schedule</div>', unsafe_allow_html=True)

view_opt = st.radio("", ["First 24 months", "By Year (summary)", "Full schedule"],
                     horizontal=True, label_visibility="collapsed")

if view_opt == "By Year (summary)":
    df_yr_full = df_amort.groupby("Year").agg(
        Rate=("Rate (%)", "first"),
        Total_Payment=("Payment", "sum"),
        Total_Principal=("Principal", "sum"),
        Total_Interest=("Interest", "sum"),
        Closing_Balance=("Balance", "last"),
        Avg_TDSR=("TDSR (%)", "mean"),
        Avg_Surplus=("Est. Surplus", "mean"),
        Rec_You=("Rec. Income You", "mean"),
        Rec_Mum=("Rec. Income Mum", "mean"),
    ).reset_index()
    df_yr_full.columns = ["Year", "Rate (%)", "Total Payment", "Principal", "Interest",
                           "Closing Balance", "Avg TDSR (%)", "Avg Surplus",
                           "Avg Rec. You", "Avg Rec. Mum"]
    df_yr_full["Rate (%)"]    = df_yr_full["Rate (%)"].map(lambda x: f"{x:.2f}%")
    df_yr_full["Avg TDSR (%)"] = df_yr_full["Avg TDSR (%)"].map(lambda x: f"{x:.1f}%")
    for c in ["Total Payment", "Principal", "Interest", "Closing Balance", "Avg Surplus", "Avg Rec. You", "Avg Rec. Mum"]:
        df_yr_full[c] = df_yr_full[c].map(lambda x: f"{x:,.0f}")
    st.dataframe(df_yr_full, use_container_width=True, hide_index=True)
else:
    df_sub = df_amort.head(24) if view_opt == "First 24 months" else df_amort
    df_show = df_sub[["Month", "Year", "Rate (%)", "Payment", "Principal", "Interest", "Balance",
                       "Rec. Income You", "Rec. Income Mum", "Joint Recognised",
                       "TDSR (%)", "Cash Mortgage", "Est. Surplus"]].copy()
    df_show["Rate (%)"]  = df_show["Rate (%)"].map(lambda x: f"{x:.2f}%")
    df_show["TDSR (%)"]  = df_show["TDSR (%)"].map(lambda x: f"{x:.1f}%")
    for c in ["Payment", "Principal", "Interest", "Balance",
              "Rec. Income You", "Rec. Income Mum", "Joint Recognised",
              "Cash Mortgage", "Est. Surplus"]:
        df_show[c] = df_show[c].map(lambda x: f"{x:,.0f}")
    st.dataframe(df_show, use_container_width=True, hide_index=True, height=420)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Full Summary</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Property & Loan**")
    st.write(f"Property Value: **{fmt_sgd(property_value)}**")
    st.write(f"Down Payment ({down_payment_pct}%): **{fmt_sgd(down_payment)}**")
    st.write(f"Loan Amount: **{fmt_sgd(loan_amount)}**")
    st.write(f"Tenor: **{loan_tenor} yrs**")
    rates_str = " → ".join([f"{r:.2f}%" for r in rate_periods])
    st.write(f"Rates: **{rates_str}**")
    st.write(f"Yr-1 Monthly Payment: **{fmt_sgd(mthly_pmt_yr1)}**")
    st.write(f"Cash: **{fmt_sgd(cash_mortgage)}/mo** · CPF: **{fmt_sgd(cpf_monthly)}/mo**")

with c2:
    st.markdown("**Year-1 Joint Income**")
    g_you = periods_you[0]["fixed"] / 12 * (1 + periods_you[0]["var_pct"] / 100)
    g_mum = periods_mum[0]["fixed"] / 12 * (1 + periods_mum[0]["var_pct"] / 100)
    st.write(f"Your Gross Monthly: **{fmt_sgd(g_you)}**")
    st.write(f"Your Tax (monthly): **{fmt_sgd(tax_you_yr1['Tax Payable']/12)}** *(eff. {tax_you_yr1['Effective Rate (%)']:.1f}%)*")
    st.write(f"Your Net Take-Home: **{fmt_sgd(net_you_mo_yr1)}**")
    st.write(f"Mum's Net Take-Home: **{fmt_sgd(net_mum_mo_yr1)}**")
    st.write(f"Joint Recognised (TDSR): **{fmt_sgd(total_rec_yr1)}**")
    st.write(f"TDSR (Yr 1): **{tdsr_yr1:.1f}%** (limit 55%)")
    st.write(f"Surplus (Yr 1): **{fmt_sgd(surplus_yr1)}/mo**")

with c3:
    st.markdown("**Cost of Borrowing**")
    st.write(f"Total Interest: **{fmt_sgd(total_interest)}**")
    st.write(f"Interest-to-Loan: **{total_interest/loan_amount*100:.1f}%**")
    st.write(f"Total Property Cost: **{fmt_sgd(total_cost)}**")
    st.write(f"Monthly Expenses: **{fmt_sgd(total_expenses)}**")
    st.write(f"Months TDSR > 55%: **{months_above_55}**")
