"""Ranz Property Model — Purchase · Affordability · Eligibility · Tax"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math, json, os
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# ── Persistence ───────────────────────────────────────────────────────────────
# On Streamlit Cloud STREAMLIT_SHARING_MODE is set; locally it is absent.
IS_CLOUD    = bool(os.environ.get("STREAMLIT_SHARING_MODE"))
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "last_inputs.json")

SAVE_KEYS = [
    "property_value","down_payment_pct","loan_tenor","extra_monthly",
    "buyer_profile","absd_remission","property_tenure",
    "sale_price","sale_agent_pct","sale_legal","sale_outstanding_mortgage","sale_holding_years",
    "include_b2","cash_b1","cash_b2","cpf_oa_b1","cpf_oa_b2",
    "variable_haircut","rental_income","rental_haircut",
    "cpf_b1","cpf_b1_pct","cpf_b2","cpf_b2_pct",
    "exp_food","exp_transport","exp_utilities","exp_insurance",
    "exp_childcare","exp_lifestyle","exp_travel","exp_family","exp_other",
    "existing_monthly_debt",
    "b1_age","num_children","spouse_working","b2_age",
    "b2_num_children","b2_spouse_working",
    "cpf_in_existing_b1","cpf_in_existing_b2","ownership_b1_pct",
    "renovation","legal_purchase","valuation_fee",
    "monthly_maintenance","lease_remaining_yrs",
]

def _collect_state():
    n = math.ceil(st.session_state.get("loan_tenor", 30) / 5)
    data = {k: st.session_state[k] for k in SAVE_KEYS if k in st.session_state}
    for k in ("loan_start", "otp_date"):
        if k in st.session_state: data[k] = str(st.session_state[k])
    for i in range(n):
        for k in [f"b1_fixed_{i}", f"b1_var_{i}", f"b2_fixed_{i}", f"b2_var_{i}", f"rate_{i}"]:
            if k in st.session_state: data[k] = st.session_state[k]
    return data

def build_save_json():
    return json.dumps(_collect_state(), indent=2)

def save_to_file():
    with open(CONFIG_FILE, "w") as f: json.dump(_collect_state(), f, indent=2)

def load_from_file():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def apply_loaded_inputs(raw: dict):
    merged = dict(BASE_DEFAULTS)
    merged.update(raw)
    for k, v in merged.items():
        st.session_state[k] = v
    for dk in ("loan_start", "otp_date"):
        val = st.session_state.get(dk)
        if isinstance(val, str):
            try: st.session_state[dk] = date.fromisoformat(val)
            except (ValueError, TypeError): pass

# Local: auto-load last_inputs.json on startup so the app remembers your session.
# Cloud: always start with hardcoded defaults; use download/upload to persist.
saved = load_from_file() if not IS_CLOUD else {}
def sv(key, default): return saved.get(key, default)

# ── Base defaults for "Fill Last Saved" button ────────────────────────────────
BASE_DEFAULTS = {
    "property_value":   2_500_000,
    "down_payment_pct": 25,
    "loan_tenor":       30,
    "renovation":       100_000,
    "sale_price":       950_000,
    "ownership_b1_pct": 50,
    "cash_b1":          100_000,
    "cpf_oa_b1":        15_000,
    "include_b2":       True,
    "cpf_b1":           1_840,
}
def parse_date(key, default="2026-08-01"):
    try: return date.fromisoformat(sv(key, default))
    except: return date.fromisoformat(default)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ranz Property Model", page_icon="🏠",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
[data-testid="stSidebar"]{background:#f0ede8;border-right:1px solid #ddd8d0;}
[data-testid="stSidebar"] *{color:#0f1923 !important;}
[data-testid="stSidebar"] .stSlider>div>div>div{background:#1e7e5c !important;}
[data-testid="stSidebar"] label{font-size:0.78rem !important;letter-spacing:0.06em;text-transform:uppercase;color:#5a7a8a !important;font-weight:600;}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#0f1923 !important;font-weight:600;}
[data-testid="stSidebar"] .stNumberInput input,[data-testid="stSidebar"] .stSelectbox select{background:#fff !important;border:1px solid #c8c0b8 !important;color:#0f1923 !important;}
[data-testid="stSidebar"] .stCheckbox label{text-transform:none !important;font-size:0.82rem !important;color:#0f1923 !important;}
[data-testid="stSidebar"] hr{border-color:#c8c0b8 !important;}
[data-testid="stSidebar"] .stCaption{color:#7a8a8a !important;font-size:0.75rem !important;}
.main .block-container{padding-top:2rem;background:#f7f4ef;}
.hero-title{font-family:'DM Serif Display',serif;font-size:2.6rem;color:#0f1923;line-height:1.1;margin-bottom:0.2rem;}
.hero-sub{font-size:0.9rem;color:#5a7a8a;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:1.5rem;}
.kpi-card{background:#fff;border-radius:12px;padding:1.2rem 1.4rem;border-left:4px solid #1e7e5c;box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-bottom:1rem;}
.kpi-card.red{border-left-color:#c0392b;}.kpi-card.amber{border-left-color:#e67e22;}
.kpi-card.blue{border-left-color:#2980b9;}.kpi-card.purple{border-left-color:#8e44ad;}
.kpi-label{font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#7a9bb5;margin-bottom:0.3rem;}
.kpi-value{font-family:'DM Serif Display',serif;font-size:1.8rem;color:#0f1923;line-height:1;}
.kpi-sub{font-size:0.73rem;color:#aaa;margin-top:0.25rem;}
.verdict-box{border-radius:12px;padding:0.9rem 1.4rem;margin-bottom:1.2rem;font-size:0.92rem;font-weight:500;}
.verdict-ok{background:#e8f8f2;color:#1a6644;border:1px solid #9fd3bc;}
.verdict-warn{background:#fef9e7;color:#7d6608;border:1px solid #f7dc6f;}
.verdict-bad{background:#fdedec;color:#922b21;border:1px solid #f1948a;}
.section-label{font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em;color:#7a9bb5;margin:1.6rem 0 0.7rem 0;border-bottom:1px solid #dde3e8;padding-bottom:0.4rem;}
.borrower-tag{display:inline-block;padding:0.15rem 0.6rem;border-radius:20px;font-size:0.78rem;font-weight:600;letter-spacing:0.05em;margin-bottom:0.5rem;}
.tag-b1{background:#d4edda;color:#1a5c2e;}.tag-b2{background:#d6eaf8;color:#1a4a6e;}
.ok-card{background:#e8f8f2;border-radius:10px;padding:12px 14px;border-left:4px solid #1e7e5c;margin-bottom:8px;font-size:13px;}
.warn-card{background:#fef9e7;border-radius:10px;padding:12px 14px;border-left:4px solid #e67e22;margin-bottom:8px;font-size:13px;}
.err-card{background:#fdedec;border-radius:10px;padding:12px 14px;border-left:4px solid #c0392b;margin-bottom:8px;font-size:13px;}
.info-card{background:#eaf4fb;border-radius:10px;padding:12px 14px;border-left:4px solid #2980b9;margin-bottom:8px;font-size:13px;}
.row-item{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #eee;font-size:13px;}
.row-label{color:#7a9bb5;}.row-total{display:flex;justify-content:space-between;padding:7px 0;font-size:14px;font-weight:700;}
.big-number{font-family:'DM Serif Display',serif;font-size:1.7rem;color:#0f1923;}
.sub-label{font-size:12px;color:#7a9bb5;}
[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden;}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def monthly_payment(principal, annual_rate, months):
    r = annual_rate / 12
    if r == 0 or months == 0: return principal / max(months, 1)
    return principal * r * (1+r)**months / ((1+r)**months - 1)

def fmt(v, d=0): return f"S${v:,.{d}f}"

def recognised_income(fixed_pa, var_pct, haircut):
    return fixed_pa/12 + (fixed_pa * var_pct/100 / 12) * haircut/100

def period_idx(yr, n): return min((yr-1)//5, n-1)

def lease_value_factor(remaining):
    """Simplified Bala's curve — fraction of freehold-equivalent value at a given remaining lease."""
    if remaining >= 79:   return 1.00
    elif remaining >= 60: return 0.88 + (remaining - 60) / 19 * 0.12
    elif remaining >= 40: return 0.63 + (remaining - 40) / 20 * 0.25
    elif remaining >= 20: return 0.32 + (remaining - 20) / 20 * 0.31
    else:                 return max(0.0, remaining / 20 * 0.32)

# ── Singapore Tax Engine (YA2024) ─────────────────────────────────────────────
TAX_BRACKETS = [(20000,0),(10000,.02),(10000,.035),(40000,.07),(40000,.115),
                (40000,.15),(40000,.18),(40000,.19),(40000,.195),(40000,.20),(1e18,.22)]

def sg_tax(ci):
    tax, rem = 0.0, max(ci, 0)
    for band, rate in TAX_BRACKETS:
        if rem <= 0: break
        tax += min(rem, band) * rate; rem -= band
    return tax

def cpf_ee_annual(gross_mo, age):
    ow = min(gross_mo, 6800)
    r  = 0.20 if age<=55 else (0.13 if age<=60 else (0.075 if age<=65 else 0.05))
    return ow * 12 * r

def compute_tax(fixed_pa, var_pa, age, n_children=0, sp_working=True):
    gross   = fixed_pa + var_pa
    cpf_ee  = cpf_ee_annual(gross/12, age)
    rel = {}
    rel["Earned Income"]       = 1000 if age<55 else (6000 if age<60 else 8000)
    rel["CPF Relief"]          = min(cpf_ee, 37740)
    if not sp_working: rel["Spouse Relief"] = 2000
    if n_children>0:   rel["Child Relief"]  = n_children * 4000
    rel["NSman (Self)"]        = 1500
    total_rel  = sum(rel.values())
    chargeable = max(gross - total_rel, 0)
    tax_before = sg_tax(chargeable)
    ptr_map    = {1:5000, 2:10000}
    ptr_total  = sum(ptr_map.get(c, 20000) for c in range(1, n_children+1))
    ptr_ann    = ptr_total / 5
    tax_pay    = max(tax_before - ptr_ann, 0)
    return {"Gross":gross,"CPF_EE":cpf_ee,"Total Relief":total_rel,
            "Chargeable":chargeable,"Tax Before Rebate":tax_before,
            "PTR":ptr_ann,"Tax Payable":tax_pay,
            "Eff Rate":tax_pay/gross*100 if gross>0 else 0,
            "reliefs": rel}

def net_monthly(period, age, n_ch=0, sp_work=True):
    fp = period["fixed"]; vp = fp * period["var_pct"]/100
    tx = compute_tax(fp, vp, age, n_ch, sp_work)
    net_pa = fp + vp - tx["CPF_EE"] - tx["Tax Payable"]
    return (fp+vp)/12, net_pa/12

# ── Stamp Duty ────────────────────────────────────────────────────────────────
def calc_bsd(p):
    brackets=[(180000,.01),(180000,.02),(640000,.03),(500000,.04),(1500000,.05),(1e18,.06)]
    bsd,rem=0,p
    for cap,r in brackets:
        t=min(rem,cap); bsd+=t*r; rem-=t
        if rem<=0: break
    return round(bsd)

def calc_ssd(p, yrs):
    if yrs<1: return round(p*.12)
    elif yrs<2: return round(p*.08)
    elif yrs<3: return round(p*.04)
    return 0

# ── Loan Schedule ─────────────────────────────────────────────────────────────
def build_loan_schedule(principal, ann_rate, years, start, extra=0):
    r = ann_rate/12; n = years*12
    pmt = (principal*r/(1-(1+r)**-n)) if r>0 else principal/n
    rows, bal, cum_int = [], principal, 0
    for i in range(1, n+1):
        interest = bal*r
        paid     = min(pmt - interest + extra, bal)
        bal     -= paid; cum_int += interest
        rows.append({"#":i,"Date":start+relativedelta(months=i-1),
                     "Beg Balance":bal+paid,"Payment":pmt+extra,
                     "Principal":paid,"Interest":interest,
                     "End Balance":max(bal,0),"Cum Interest":cum_int})
        if bal<=0: break
    df = pd.DataFrame(rows); df["Date"]=pd.to_datetime(df["Date"])
    return df, pmt, cum_int

# ── Dynamic Amortisation ──────────────────────────────────────────────────────
def amortise_dynamic(principal, rate_periods, tenor_yrs,
                     p_b1, p_b2, haircut,
                     cpf_b1, pct_b1, cpf_b2, pct_b2,
                     expenses, debt, rental_rec,
                     b1_age, b2_age, n_ch, sp_work,
                     b2_n_ch=0, b2_sp_work=True):
    months  = tenor_yrs*12
    cpf_mo  = cpf_b1*pct_b1/100 + cpf_b2*pct_b2/100
    n_rp    = len(rate_periods); n_b1=len(p_b1); n_b2=len(p_b2)
    rows, bal, pmt = [], principal, 0
    for m in range(1, months+1):
        yr  = (m-1)//12+1
        ri  = period_idx(yr, n_rp)
        r_a = rate_periods[ri]/100; r_m = r_a/12
        if m==1 or (m-1)%60==0:
            rem = months-m+1
            pmt = (bal*r_m*(1+r_m)**rem/((1+r_m)**rem-1)) if r_m>0 else bal/rem
        interest = bal*r_m; princ = pmt-interest; bal = max(bal-princ,0)
        cash_pmt = max(pmt-cpf_mo,0)
        pb1 = p_b1[period_idx(yr,n_b1)]; pb2 = p_b2[period_idx(yr,n_b2)]
        rec_b1 = recognised_income(pb1["fixed"],pb1["var_pct"],haircut)
        rec_b2 = recognised_income(pb2["fixed"],pb2["var_pct"],haircut)
        total_rec = rec_b1+rec_b2+rental_rec
        tdsr = (pmt+debt)/total_rec*100 if total_rec>0 else 999
        _, nb1 = net_monthly(pb1, b1_age+(yr-1), n_ch, sp_work)
        _, nb2 = net_monthly(pb2, b2_age+(yr-1), b2_n_ch, b2_sp_work)
        surplus = nb1+nb2-cash_pmt-expenses-debt
        rows.append({"Month":m,"Year":yr,"Rate":r_a*100,"Payment":pmt,
                     "Principal":princ,"Interest":interest,"Balance":bal,
                     "Rec B1":rec_b1,"Rec B2":rec_b2,"Joint Rec":total_rec,
                     "TDSR":tdsr,"Cash Mortgage":cash_pmt,"Surplus":surplus})
    return pd.DataFrame(rows)

# ── TDSR max loan ─────────────────────────────────────────────────────────────
STRESS = 0.04
def tdsr_max_loan(gross_mo, other_debt_mo, years, limit=0.55):
    r=STRESS/12; n=years*12; mp=gross_mo*limit-other_debt_mo
    if mp<=0: return 0
    return round(mp*(1-(1+r)**-n)/r)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def _fl(base, key, default=0):
    """Append comma-formatted current value to a number_input label."""
    v = st.session_state.get(key, default)
    if isinstance(v, (int, float)) and abs(v) >= 1000:
        return f"{base}  —  S${int(v):,}"
    return base
with st.sidebar:
    st.markdown("## 🏠 Inputs")

    # ── Load / Save ────────────────────────────────────────────────────────────
    if IS_CLOUD:
        # Cloud: download JSON to save; upload JSON to restore
        _uploaded = st.file_uploader("📂 Load saved inputs (JSON)", type="json",
                                      label_visibility="collapsed", key="json_uploader",
                                      help="Upload a previously saved last_inputs.json")
        st.caption("⬆ Upload JSON to restore · ⬇ Download to save")
        if _uploaded is not None:
            _uid = (_uploaded.name, _uploaded.size)
            if st.session_state.get("_last_upload_id") != _uid:
                st.session_state["_last_upload_id"] = _uid
                apply_loaded_inputs(json.load(_uploaded))
                st.rerun()
        st.download_button("💾 Save Inputs", data=build_save_json(),
                           file_name="last_inputs.json", mime="application/json",
                           use_container_width=True,
                           help="Download current inputs as JSON to reload later")
    else:
        # Local: auto-saves to last_inputs.json; button writes immediately
        if st.button("💾 Save Inputs", use_container_width=True,
                     help="Save current inputs to last_inputs.json"):
            save_to_file()
            st.success("✅ Saved")

    st.markdown("### Property & Loan")
    property_value   = st.number_input(_fl("Property Value (SGD)","property_value",2_500_000), value=sv("property_value",2_500_000), step=50_000, format="%d", key="property_value")
    down_pct         = st.slider("Down Payment (%)", 5, 75, sv("down_payment_pct",25), key="down_payment_pct")
    loan_tenor       = st.slider("Loan Tenor (years)", 5, 35, sv("loan_tenor",30), key="loan_tenor")
    extra_monthly    = st.number_input(_fl("Extra Monthly Repayment","extra_monthly",0), value=sv("extra_monthly",0), step=500, format="%d", key="extra_monthly")
    renovation       = st.number_input(_fl("Renovation","renovation",100_000), value=sv("renovation",100_000), step=10_000, format="%d", key="renovation")
    legal_purchase   = st.number_input(_fl("Legal Fees — Purchase","legal_purchase",3_500), value=sv("legal_purchase",3_500), step=500, format="%d", key="legal_purchase")
    valuation_fee    = st.number_input(_fl("Valuation Fee","valuation_fee",500), value=sv("valuation_fee",500), step=100, format="%d", key="valuation_fee")
    loan_start       = st.date_input("Loan Start Date", value=parse_date("loan_start","2026-08-01"), key="loan_start")
    otp_date         = st.date_input("OTP Date", value=parse_date("otp_date","2026-08-01"), key="otp_date")
    property_tenure  = st.selectbox("Property Tenure",
                                    ["Freehold","99-yr Leasehold (new / ≥60yr left)","99-yr Leasehold (30–59yr left)","99-yr Leasehold (<30yr left)"],
                                    index=["Freehold","99-yr Leasehold (new / ≥60yr left)","99-yr Leasehold (30–59yr left)","99-yr Leasehold (<30yr left)"].index(
                                        sv("property_tenure","Freehold")), key="property_tenure")
    monthly_maintenance = st.number_input(_fl("Monthly Maintenance Fee","monthly_maintenance",500), value=sv("monthly_maintenance",500), step=50, format="%d", key="monthly_maintenance",
                                           help="Condo MC fee, sinking fund, or landed maintenance. Used in Exit Strategy tab.")
    is_leasehold = "Leasehold" in property_tenure
    if is_leasehold:
        _lr_default = 90 if "new" in property_tenure or "≥60" in property_tenure else (45 if "30–59" in property_tenure else 20)
        lease_remaining_yrs = st.slider("Remaining Lease (years)", 1, 99, sv("lease_remaining_yrs", _lr_default), key="lease_remaining_yrs")
    else:
        lease_remaining_yrs = 999
    st.caption("💡 Interest rates set per 5-year period in the schedule below.")

    st.markdown("### Stamp Duty")
    ABSD_OPTIONS = {
        "SC — 1st property (0%)":0.0,"SC — 2nd property (20%)":0.20,
        "SC — 3rd+ property (30%)":0.30,"SPR — 1st property (5%)":0.05,
        "SPR — 2nd+ property (25%)":0.25,"Foreigner (60%)":0.60,
    }
    buyer_profile  = st.selectbox("Buyer Profile", list(ABSD_OPTIONS),
                                   index=list(ABSD_OPTIONS).index(sv("buyer_profile","SC — 2nd property (20%)")),
                                   key="buyer_profile")
    absd_rate      = ABSD_OPTIONS[buyer_profile]
    absd_remission = st.checkbox("ABSD remission eligible?", value=sv("absd_remission",True), key="absd_remission",
                                  help="SC married couple: refunded if existing property sold within 6 months of completion.")

    st.markdown("### Property Sale")
    sale_price       = st.number_input(_fl("Sale Price","sale_price",950_000), value=sv("sale_price",950_000), step=10_000, format="%d", key="sale_price")
    sale_agent_pct   = st.number_input("Agent Commission (%)", value=sv("sale_agent_pct",1.0), step=0.25, format="%.2f", key="sale_agent_pct")
    sale_legal       = st.number_input(_fl("Legal Fees — Sale","sale_legal",2_500), value=sv("sale_legal",2_500), step=500, format="%d", key="sale_legal")
    sale_outstanding = st.number_input(_fl("Outstanding Mortgage","sale_outstanding_mortgage",360_000), value=sv("sale_outstanding_mortgage",360_000), step=10_000, format="%d", key="sale_outstanding_mortgage")
    sale_held_yrs    = st.number_input("Years Held (SSD)", value=sv("sale_holding_years",4.0), step=0.5, format="%.1f", key="sale_holding_years")
    st.caption("CPF refund on sale (principal + accrued interest at 2.5% p.a.)")
    cpf_in_existing_b1 = st.number_input(_fl("CPF Used in Existing Property — B1","cpf_in_existing_b1",150_000), value=sv("cpf_in_existing_b1",150_000), step=5_000, format="%d", key="cpf_in_existing_b1",
                                          help="Total CPF OA withdrawn (principal only). Accrued interest calculated automatically.")
    cpf_in_existing_b2 = st.number_input(_fl("CPF Used in Existing Property — B2","cpf_in_existing_b2",0), value=sv("cpf_in_existing_b2",0), step=5_000, format="%d", key="cpf_in_existing_b2")
    ownership_b1_pct   = st.slider("Ownership Share — B1 (%)", 1, 100, sv("ownership_b1_pct",50), key="ownership_b1_pct",
                                    help="B1 share of net sale proceeds after CPF refunds")

    st.markdown("### Cash & CPF Sources")
    cash_b1   = st.number_input(_fl("Cash Savings — B1","cash_b1",100_000), value=sv("cash_b1",100_000), step=10_000, format="%d", key="cash_b1")
    cpf_oa_b1 = st.number_input(_fl("CPF OA Balance — B1","cpf_oa_b1",15_000), value=sv("cpf_oa_b1",15_000), step=1_000, format="%d", key="cpf_oa_b1",
                                 help="One-time OA balance for down payment")
    st.markdown("---")
    include_b2 = st.toggle("🤝 Joint Borrower 2", value=bool(sv("include_b2", True)), key="include_b2")
    if include_b2:
        cash_b2   = st.number_input(_fl("Cash Savings — B2","cash_b2",60_000), value=sv("cash_b2",60_000), step=10_000, format="%d", key="cash_b2")
        cpf_oa_b2 = st.number_input(_fl("CPF OA Balance — B2","cpf_oa_b2",0), value=sv("cpf_oa_b2",0), step=1_000, format="%d", key="cpf_oa_b2")
    else:
        cash_b2 = 0; cpf_oa_b2 = 0

    st.markdown("### Variable Income & Rental")
    variable_haircut = st.slider("Variable Income Recognised (%)", 0, 100, sv("variable_haircut",70), key="variable_haircut",
                                  help="~70% is standard SG bank practice")
    rental_income    = st.number_input(_fl("Rental Income p.a.","rental_income",0), value=sv("rental_income",0), step=1_000, format="%d", key="rental_income")
    rental_haircut   = st.slider("Rental Credit (%)", 0, 100, sv("rental_haircut",70), key="rental_haircut")

    st.markdown("### CPF — Borrower 1 (monthly)")
    cpf_b1     = st.number_input(_fl("Monthly CPF OA Contribution","cpf_b1",1_840), value=sv("cpf_b1",1_840), step=100, format="%d", key="cpf_b1")
    cpf_b1_pct = st.slider("CPF for Mortgage (%)", 0, 100, sv("cpf_b1_pct",100), key="cpf_b1_pct")

    if include_b2:
        st.markdown("### CPF — Borrower 2 (monthly)")
        cpf_b2     = st.number_input(_fl("Monthly CPF OA Contribution","cpf_b2",600), value=sv("cpf_b2",600), step=100, format="%d", key="cpf_b2")
        cpf_b2_pct = st.slider("CPF for Mortgage (%)", 0, 100, sv("cpf_b2_pct",60), key="cpf_b2_pct")
    else:
        cpf_b2 = 0; cpf_b2_pct = 0

    st.markdown("### Monthly Expenses")
    exp_food      = st.number_input("Food & Groceries",         value=sv("exp_food",1_000),      step=100, format="%d", key="exp_food")
    exp_transport = st.number_input("Transport / Car",           value=sv("exp_transport",1_000), step=100, format="%d", key="exp_transport")
    exp_utilities = st.number_input("Utilities & Telco",         value=sv("exp_utilities",1_000), step=50,  format="%d", key="exp_utilities")
    exp_insurance = st.number_input("Insurance Premiums",        value=sv("exp_insurance",1_000), step=100, format="%d", key="exp_insurance")
    exp_childcare = st.number_input("Childcare / Education",     value=sv("exp_childcare",1_000), step=100, format="%d", key="exp_childcare")
    exp_lifestyle = st.number_input("Lifestyle & Entertainment", value=sv("exp_lifestyle",1_000), step=100, format="%d", key="exp_lifestyle")
    exp_travel    = st.number_input("Travel (monthly amort.)",   value=sv("exp_travel",1_000),    step=100, format="%d", key="exp_travel")
    exp_family    = st.number_input("Family Support",            value=sv("exp_family",1_000),    step=100, format="%d", key="exp_family")
    exp_other     = st.number_input("Other / Misc",              value=sv("exp_other",1_000),     step=100, format="%d", key="exp_other")

    st.markdown("### Existing Debt")
    existing_debt = st.number_input("Other Monthly Debt", value=sv("existing_monthly_debt",0), step=100, format="%d", key="existing_monthly_debt")

    st.markdown("### Tax Profile — Borrower 1")
    b1_age       = st.slider("B1 Age", 22, 65, sv("b1_age",33), key="b1_age")
    num_children = st.slider("Number of Children", 0, 5, sv("num_children",2), key="num_children")
    spouse_work  = st.checkbox("Spouse working / income > SGD 4k p.a.", value=sv("spouse_working",True), key="spouse_working")

    if include_b2:
        st.markdown("### Tax Profile — Borrower 2")
        b2_age          = st.slider("B2 Age", 22, 75, sv("b2_age",58), key="b2_age")
        b2_num_children = st.slider("B2 Number of Children", 0, 5, sv("b2_num_children",0), key="b2_num_children")
        b2_spouse_work  = st.checkbox("B2 Spouse working / income > SGD 4k p.a.", value=sv("b2_spouse_working",True), key="b2_spouse_working")
    else:
        b2_age = b1_age
        b2_num_children = 0
        b2_spouse_work  = True


# ─────────────────────────────────────────────────────────────────────────────
# INCOME & RATE SCHEDULE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Ranz Property Model</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Purchase · Affordability · Eligibility · Tax · Singapore</div>', unsafe_allow_html=True)

num_periods   = math.ceil(loan_tenor/5)
period_labels = [f"Yr {i*5+1}–{min((i+1)*5, loan_tenor)}" for i in range(num_periods)]

periods_b1, periods_b2, rate_periods = [], [], []

with st.expander("📅 Income & Rate Schedule — 5-Year Periods", expanded=True):
    st.caption("Edit each borrower's salary and the interest rate per 5-year window. Mortgage recalculates at each rate change.")
    sched_tabs = st.tabs(period_labels)
    for i, tab in enumerate(sched_tabs):
        with tab:
            default_rates = [1.6, 1.8, 2.4, 2.6, 2.6]
            r_i = st.slider("🏦 Interest Rate (% p.a.)", 1.0, 7.0,
                             float(sv(f"rate_{i}", default_rates[i] if i<5 else 3.5)),
                             step=0.05, key=f"rate_{i}")
            rate_periods.append(r_i)
            st.markdown("---")
            if include_b2:
                cb1, cb2 = st.columns(2)
            else:
                cb1 = st.container()
            with cb1:
                st.markdown('<span class="borrower-tag tag-b1">👤 Borrower 1</span>', unsafe_allow_html=True)
                fb1 = st.number_input(_fl("Fixed p.a.", f"b1_fixed_{i}", 100_000), value=sv(f"b1_fixed_{i}", 100_000),
                                       step=5000, format="%d", key=f"b1_fixed_{i}")
                vb1 = st.slider("Bonus %", 0, 150, sv(f"b1_var_{i}", 0), key=f"b1_var_{i}")
                periods_b1.append({"fixed": fb1, "var_pct": vb1})
            if include_b2:
                with cb2:
                    st.markdown('<span class="borrower-tag tag-b2">👩 Borrower 2</span>', unsafe_allow_html=True)
                    fb2 = st.number_input(_fl("Fixed p.a.", f"b2_fixed_{i}", 100_000), value=sv(f"b2_fixed_{i}", 100_000),
                                           step=5000, format="%d", key=f"b2_fixed_{i}")
                    vb2 = st.slider("Bonus %", 0, 150, sv(f"b2_var_{i}", 0), key=f"b2_var_{i}")
                    periods_b2.append({"fixed": fb2, "var_pct": vb2})
            else:
                periods_b2.append({"fixed": 0, "var_pct": 0})

# ─────────────────────────────────────────────────────────────────────────────
# CORE CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────
down_payment  = property_value * down_pct / 100
loan_amount   = property_value - down_payment
months_total  = loan_tenor * 12
ir_yr1        = rate_periods[0]
pmt_yr1       = monthly_payment(loan_amount, ir_yr1/100, months_total)
cpf_monthly   = cpf_b1*cpf_b1_pct/100 + cpf_b2*cpf_b2_pct/100
cash_mortgage = max(pmt_yr1 - cpf_monthly, 0)
total_exp     = sum([exp_food,exp_transport,exp_utilities,exp_insurance,
                     exp_childcare,exp_lifestyle,exp_travel,exp_family,exp_other])
rental_rec    = (rental_income/12) * rental_haircut/100

# Stamp duty & sale
bsd          = calc_bsd(property_value)
absd         = round(property_value * absd_rate)
absd_upfront = absd
absd_net     = 0 if (absd_remission and absd_rate>0) else absd
stamp_total  = bsd + absd_net
ssd          = calc_ssd(sale_price, sale_held_yrs)
sale_agent   = round(sale_price * sale_agent_pct/100)
sale_gross_proceeds = sale_price - sale_agent - sale_legal - ssd - sale_outstanding
# CPF accrued interest: 2.5% p.a. compounded monthly over holding period
_cpf_months = sale_held_yrs * 12
_cpf_factor = (1 + 0.025/12) ** _cpf_months - 1  # interest-only factor
cpf_accrued_b1 = round(cpf_in_existing_b1 * _cpf_factor)
cpf_accrued_b2 = round((cpf_in_existing_b2 if include_b2 else 0) * _cpf_factor)
cpf_refund_b1  = cpf_in_existing_b1 + cpf_accrued_b1
cpf_refund_b2  = (cpf_in_existing_b2 if include_b2 else 0) + cpf_accrued_b2
total_cpf_refund = cpf_refund_b1 + cpf_refund_b2
cash_after_cpf   = sale_gross_proceeds - total_cpf_refund
_b2_share        = (100 - ownership_b1_pct) / 100
_b1_share        = ownership_b1_pct / 100
cash_to_b1 = round(max(cash_after_cpf * _b1_share, 0))
cash_to_b2 = round(max(cash_after_cpf * _b2_share, 0)) if include_b2 else 0
sale_proceeds = sale_gross_proceeds  # keep existing variable for down-payment calc

total_home_cost      = property_value + bsd + absd_net + legal_purchase + valuation_fee + renovation
total_cash_available = cash_b1 + cash_b2 + cpf_oa_b1 + cpf_oa_b2 + sale_proceeds
cash_surplus         = total_cash_available + loan_amount - total_home_cost
ltv                  = loan_amount / property_value
min_cash_req         = property_value * 0.05
cash_only            = cash_b1 + cash_b2  # no CPF for 5% check

# Income / tax year 1
f_b1_yr1 = periods_b1[0]["fixed"]; v_b1_yr1 = f_b1_yr1 * periods_b1[0]["var_pct"]/100
f_b2_yr1 = periods_b2[0]["fixed"]; v_b2_yr1 = f_b2_yr1 * periods_b2[0]["var_pct"]/100
tx_b1_yr1 = compute_tax(f_b1_yr1, v_b1_yr1, b1_age, num_children, spouse_work)
tx_b2_yr1 = compute_tax(f_b2_yr1, v_b2_yr1, b2_age, b2_num_children, b2_spouse_work)
_, net_b1_yr1 = net_monthly(periods_b1[0], b1_age, num_children, spouse_work)
_, net_b2_yr1 = net_monthly(periods_b2[0], b2_age, b2_num_children, b2_spouse_work)
net_home_yr1  = net_b1_yr1 + net_b2_yr1

rec_b1_yr1    = recognised_income(f_b1_yr1, periods_b1[0]["var_pct"], variable_haircut)
rec_b2_yr1    = recognised_income(f_b2_yr1, periods_b2[0]["var_pct"], variable_haircut)
total_rec_yr1 = rec_b1_yr1 + rec_b2_yr1 + rental_rec
tdsr_yr1      = (pmt_yr1 + existing_debt) / total_rec_yr1 * 100 if total_rec_yr1>0 else 999
stress_pmt    = monthly_payment(loan_amount, STRESS, months_total)
tdsr_stress   = (stress_pmt + existing_debt) / total_rec_yr1 * 100 if total_rec_yr1>0 else 999
surplus_yr1   = net_home_yr1 - cash_mortgage - total_exp - existing_debt

# Full amortisation
df_amort = amortise_dynamic(
    loan_amount, rate_periods, loan_tenor,
    periods_b1, periods_b2, variable_haircut,
    cpf_b1, cpf_b1_pct, cpf_b2, cpf_b2_pct,
    total_exp, existing_debt, rental_rec,
    b1_age, b2_age, num_children, spouse_work,
    b2_num_children, b2_spouse_work)
total_interest = df_amort["Interest"].sum()
total_cost     = loan_amount + total_interest + down_payment

# Fixed-rate loan schedule (for tabs 7)
df_loan, pmt_sched, int_sched = build_loan_schedule(
    loan_amount, ir_yr1/100, loan_tenor, loan_start, extra_monthly)

# Per-year arrays
years = list(range(1, loan_tenor+1))
rec_b1_yr = [recognised_income(periods_b1[period_idx(y,num_periods)]["fixed"],
                                periods_b1[period_idx(y,num_periods)]["var_pct"],
                                variable_haircut) for y in years]
rec_b2_yr = [recognised_income(periods_b2[period_idx(y,num_periods)]["fixed"],
                                periods_b2[period_idx(y,num_periods)]["var_pct"],
                                variable_haircut) for y in years]
joint_rec_yr = [a+b+rental_rec for a,b in zip(rec_b1_yr, rec_b2_yr)]

pmt_by_yr = []
_bal = loan_amount
for y in years:
    ri = period_idx(y, len(rate_periods))
    rm = rate_periods[ri]/100/12
    rem = months_total - (y-1)*12
    _pmt = (_bal*rm*(1+rm)**rem/((1+rm)**rem-1)) if rm>0 and rem>0 else (_bal/rem if rem>0 else 0)
    pmt_by_yr.append(_pmt)
    for _ in range(12):
        if _bal<=0: break
        _bal = max(_bal - (_pmt - _bal*rm), 0)

tdsr_yr       = [(pmt_by_yr[i]+existing_debt)/joint_rec_yr[i]*100 if joint_rec_yr[i]>0 else 999 for i in range(len(years))]
cash_mtg_yr   = [max(p-cpf_monthly,0) for p in pmt_by_yr]
surplus_by_yr = []
for i,y in enumerate(years):
    _, nb1 = net_monthly(periods_b1[period_idx(y,num_periods)], b1_age+(y-1), num_children, spouse_work)
    _, nb2 = net_monthly(periods_b2[period_idx(y,num_periods)], b2_age+(y-1), b2_num_children, b2_spouse_work)
    surplus_by_yr.append(nb1+nb2-cash_mtg_yr[i]-total_exp-existing_debt)

# ── Regulatory checks
_ages_for_ltv      = [b1_age, b2_age] if include_b2 else [b1_age]
max_ltv_age_capped = (loan_tenor>30) or (max(_ages_for_ltv)+loan_tenor>65)
ltv_limit    = 0.55 if max_ltv_age_capped else 0.75
ltv_ok       = ltv <= ltv_limit
min_cash_ok  = cash_only >= min_cash_req
tdsr_stress_ok = tdsr_stress <= 55
tenure_ok    = loan_tenor <= 35

# ── Verdict (affordability)
months_over55 = int((df_amort["TDSR"]>55).sum())
if tdsr_yr1<=40 and months_over55==0:
    vc,vi = "verdict-ok","✅"
    vm = f"Year-1 TDSR {tdsr_yr1:.1f}% — well within MAS 55% limit."
elif tdsr_yr1<=55:
    vc,vi = "verdict-warn","⚠️"
    vm = f"Year-1 TDSR {tdsr_yr1:.1f}% — within limit but stretched."
    if months_over55: vm += f" TDSR breaches 55% in {months_over55} future month(s)."
else:
    vc,vi = "verdict-bad","🚫"
    vm = f"Year-1 TDSR {tdsr_yr1:.1f}% — EXCEEDS MAS 55% limit."

st.markdown(f'<div class="verdict-box {vc}">{vi} {vm}</div>', unsafe_allow_html=True)

k1,k2,k3,k4 = st.columns(4)
k1.markdown(f"""<div class="kpi-card">
  <div class="kpi-label">Monthly Mortgage (Yr 1)</div>
  <div class="kpi-value">{fmt(pmt_yr1)}</div>
  <div class="kpi-sub">Cash {fmt(cash_mortgage)} · CPF {fmt(cpf_monthly)} · {ir_yr1:.2f}%</div>
</div>""", unsafe_allow_html=True)

tc = "red" if tdsr_yr1>55 else ("amber" if tdsr_yr1>40 else "")
k2.markdown(f"""<div class="kpi-card {tc}">
  <div class="kpi-label">TDSR Year 1</div>
  <div class="kpi-value">{tdsr_yr1:.1f}%</div>
  <div class="kpi-sub">Stress-test: {tdsr_stress:.1f}% · MAS limit 55%</div>
</div>""", unsafe_allow_html=True)

sc = "red" if surplus_yr1<0 else "blue"
k3.markdown(f"""<div class="kpi-card {sc}">
  <div class="kpi-label">Monthly Surplus (Yr 1)</div>
  <div class="kpi-value">{fmt(surplus_yr1)}</div>
  <div class="kpi-sub">After tax, CPF, mortgage & expenses</div>
</div>""", unsafe_allow_html=True)

xc = "red" if cash_surplus<0 else ""
k4.markdown(f"""<div class="kpi-card {xc}">
  <div class="kpi-label">Cash Surplus / (Shortfall)</div>
  <div class="kpi-value">{fmt(cash_surplus)}</div>
  <div class="kpi-sub">Total interest: {fmt(total_interest)}</div>
</div>""", unsafe_allow_html=True)

# ── Scenario builder (shared by Cash Timeline tab) ───────────────────────────
def build_scenario(otp_pct, ex_pct, opt_wks, own_at_start):
    otp_fee  = round(property_value*otp_pct)
    ex_fee   = round(property_value*ex_pct)
    comp_due = max(property_value - loan_amount - otp_fee - ex_fee, 0)
    ex_date        = otp_date + timedelta(weeks=opt_wks)
    bsd_date       = ex_date  + timedelta(days=14)
    comp_date      = ex_date  + timedelta(weeks=12)
    absd_ref_date  = comp_date + timedelta(days=180)
    tl, cum = [], 0
    for desc,amt in [("Cash B1",cash_b1),("CPF OA B1",cpf_oa_b1)]+([("Cash B2",cash_b2),("CPF OA B2",cpf_oa_b2)] if include_b2 else []):
        cum+=amt; tl.append({"Stage":"Starting Cash","Date":otp_date,"Desc":desc,"In":amt,"Out":0,"Cum":cum})
    if own_at_start:
        cum+=sale_proceeds; tl.append({"Stage":"Starting Cash","Date":otp_date,"Desc":"Property sale proceeds","In":sale_proceeds,"Out":0,"Cum":cum})
    for desc,amt,dt in [("Option fee",otp_fee,otp_date),("Legal fees",legal_purchase,otp_date),("Valuation",valuation_fee,otp_date)]:
        cum-=amt; tl.append({"Stage":"OTP","Date":dt,"Desc":desc,"In":0,"Out":amt,"Cum":cum})
    if not own_at_start:
        sd = otp_date+timedelta(weeks=max(1,int(opt_wks*0.85)))
        cum+=sale_proceeds; tl.append({"Stage":"House Sale","Date":sd,"Desc":"Property sale proceeds","In":sale_proceeds,"Out":0,"Cum":cum})
    for desc,amt,dt in [("Exercise fee",ex_fee,ex_date),("BSD",bsd,bsd_date)]:
        cum-=amt; tl.append({"Stage":"Exercise","Date":dt,"Desc":desc,"In":0,"Out":amt,"Cum":cum})
    if absd_upfront>0:
        cum-=absd_upfront; tl.append({"Stage":"Exercise","Date":bsd_date,"Desc":f"ABSD ({absd_rate:.0%}) upfront","In":0,"Out":absd_upfront,"Cum":cum})
    cum-=comp_due; tl.append({"Stage":"Completion","Date":comp_date,"Desc":"Balance downpayment","In":0,"Out":comp_due,"Cum":cum})
    if absd_remission and absd_upfront>0:
        cum+=absd_upfront; tl.append({"Stage":"ABSD Refund","Date":absd_ref_date,"Desc":"ABSD refund","In":absd_upfront,"Out":0,"Cum":cum})
    cum-=renovation; tl.append({"Stage":"Post-Completion","Date":comp_date+timedelta(days=30),"Desc":"Renovation","In":0,"Out":renovation,"Cum":cum})
    return pd.DataFrame(tl), cum

df_s1, fin_s1 = build_scenario(0.01,0.04,2,True)
df_s2, fin_s2 = build_scenario(0.04,0.01,12,False)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
(tab_purch, tab_elig, tab_reg, tab_tl,
 tab_aff,   tab_tax,  tab_loan, tab_sd, tab_sens, tab_exit) = st.tabs([
    "📊 Purchase Summary",
    "🏦 Mortgage Eligibility",
    "⚠️ Regulatory Checks",
    "📅 Cash Timeline",
    "💰 Affordability & Cashflow",
    "🧾 Tax Analysis",
    "💳 Loan Schedule",
    "📐 Stamp Duty",
    "📈 Sensitivity",
    "🚪 Exit Strategy",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PURCHASE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab_purch:
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="section-label">Purchase Costs</div>', unsafe_allow_html=True)
        for label,val in [("Property Price",property_value),("BSD",bsd),
                           (f"ABSD ({absd_rate:.0%})"+("+remission" if absd_remission and absd>0 else ""),absd_net),
                           ("Legal + Valuation",legal_purchase+valuation_fee),("Renovation",renovation)]:
            st.markdown(f'<div class="row-item"><span class="row-label">{label}</span><span>{fmt(val)}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-total"><span>Total Cost</span><span style="color:#2980b9">{fmt(total_home_cost)}</span></div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-label">Cash Sources</div>', unsafe_allow_html=True)
        _own_src = [("Cash B1", cash_b1), ("CPF OA B1", cpf_oa_b1)]
        if include_b2: _own_src += [("Cash B2", cash_b2), ("CPF OA B2", cpf_oa_b2)]
        _own_src += [(f"Property Sale (SSD {fmt(ssd)})", sale_proceeds)]
        own_funds = sum(v for _, v in _own_src)
        for label, val in _own_src:
            c = "color:#c0392b" if val < 0 else ""
            st.markdown(f'<div class="row-item"><span class="row-label">{label}</span><span style="{c}">{fmt(val)}</span></div>', unsafe_allow_html=True)
        own_clr = "#1e7e5c" if own_funds >= down_payment else "#c0392b"
        st.markdown(f'<div class="row-total"><span>Own Funds</span><span style="color:{own_clr}">{fmt(own_funds)}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-item" style="margin-top:6px"><span class="row-label">+ Loan Amount (TDSR-limited)</span><span>{fmt(loan_amount)}</span></div>', unsafe_allow_html=True)
        clr = "#1e7e5c" if cash_surplus >= 0 else "#c0392b"
        st.markdown(f'<div class="row-total"><span>Surplus / (Shortfall)</span><span style="color:{clr}">{fmt(cash_surplus)}</span></div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="section-label">Financing</div>', unsafe_allow_html=True)
        for label,val in [("Loan Amount",fmt(loan_amount)),
                           (f"LTV (limit {ltv_limit:.0%})",f"{ltv:.1%}"),
                           ("Down Payment",fmt(down_payment)),
                           ("5% Min Cash",fmt(min_cash_req)),
                           ("Monthly Payment (Yr 1)",fmt(pmt_yr1)),
                           ("Stress Payment (4%)",fmt(stress_pmt)),
                           (f"TDSR stress-tested",f"{tdsr_stress:.1f}%"),
                           ("Total Interest",fmt(total_interest))]:
            clr = ""
            if "TDSR" in label: clr = "color:#1e7e5c" if tdsr_stress_ok else "color:#c0392b"
            if "LTV" in label:  clr = "color:#1e7e5c" if ltv_ok else "color:#c0392b"
            st.markdown(f'<div class="row-item"><span class="row-label">{label}</span><span style="{clr}">{val}</span></div>', unsafe_allow_html=True)

    # ── Sale Proceeds Breakdown ────────────────────────────────────────────────
    with st.expander("🏦 Existing Property Sale — Proceeds Breakdown", expanded=False):
        st.caption("How the sale proceeds are distributed between CPF refunds and cash to each borrower.")
        sp1, sp2 = st.columns(2)

        with sp1:
            st.markdown("**Gross Proceeds**")
            for label, val in [
                ("Sale Price",        sale_price),
                ("Agent Commission",  -sale_agent),
                ("Legal Fees",        -sale_legal),
                ("SSD",               -ssd),
                ("Outstanding Loan",  -sale_outstanding),
            ]:
                clr = "color:#c0392b" if val < 0 else ""
                st.markdown(f'<div class="row-item"><span class="row-label">{label}</span>'
                            f'<span style="{clr}">{fmt(abs(val)) if val<0 else fmt(val)}</span></div>',
                            unsafe_allow_html=True)
            clr2 = "#1e7e5c" if sale_gross_proceeds >= 0 else "#c0392b"
            st.markdown(f'<div class="row-total"><span>Gross Proceeds</span>'
                        f'<span style="color:{clr2}">{fmt(sale_gross_proceeds)}</span></div>',
                        unsafe_allow_html=True)

        with sp2:
            st.markdown("**CPF Refund & Cash Split**")
            cpf_rows = [("CPF Used — B1", cpf_in_existing_b1),
                        (f"Accrued Interest — B1 ({sale_held_yrs:.1f}yr @ 2.5%)", cpf_accrued_b1),
                        ("CPF Refund → B1 OA", -cpf_refund_b1)]
            if include_b2:
                cpf_rows += [("CPF Used — B2", cpf_in_existing_b2),
                             (f"Accrued Interest — B2", cpf_accrued_b2),
                             ("CPF Refund → B2 OA", -cpf_refund_b2)]
            cpf_rows.append(("Cash After CPF Refund", cash_after_cpf))
            for label, val in cpf_rows:
                clr = "color:#c0392b" if val < 0 else ("color:#2980b9" if "Refund →" in label else "")
                st.markdown(f'<div class="row-item"><span class="row-label">{label}</span>'
                            f'<span style="{clr}">{fmt(abs(val)) if val<0 else fmt(val)}</span></div>',
                            unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(f"**Ownership split: B1 {ownership_b1_pct}%"
                        + (f" / B2 {100-ownership_b1_pct}%" if include_b2 else "") + "**")
            st.markdown(f'<div class="row-total"><span>Cash to B1</span>'
                        f'<span style="color:#1e7e5c">{fmt(cash_to_b1)}</span></div>',
                        unsafe_allow_html=True)
            if include_b2:
                st.markdown(f'<div class="row-total"><span>Cash to B2</span>'
                            f'<span style="color:#1e7e5c">{fmt(cash_to_b2)}</span></div>',
                            unsafe_allow_html=True)
            st.caption("Cash adds to each borrower's available funds for the new purchase.")

    st.markdown('<div class="section-label">Break-even Appreciation</div>', unsafe_allow_html=True)
    purchase_costs_ex = bsd + absd_net + legal_purchase + valuation_fee + renovation
    be_rows = []
    for yrs in [3,5,7,10,15]:
        cum_int = df_loan[df_loan["#"]<=yrs*12]["Interest"].sum()
        be1 = cum_int / property_value
        be2 = (cum_int + purchase_costs_ex) / property_value
        be_rows.append({
            "Hold Period": f"{yrs}yr",
            "Cum Interest": fmt(cum_int),
            "Need (int only)":  f"{be1:.1%}",
            "CAGR (int only)": f"{(1+be1)**(1/yrs)-1:.2%}",
            "Need (all-in)":   f"{be2:.1%}",
            "CAGR (all-in)":   f"{(1+be2)**(1/yrs)-1:.2%}",
        })
    st.dataframe(pd.DataFrame(be_rows), use_container_width=True, hide_index=True)

    # ── Exit & Return Analysis ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">Exit & Return Analysis</div>', unsafe_allow_html=True)
    st.caption("Model your net return at different exit years and appreciation assumptions. "
               "Selling costs assumed at 2% (agent + legal). CPF refund estimated at principal + 2.5% p.a. accrued.")

    ea_col, ea_chart = st.columns([1, 2])
    with ea_col:
        app_rate = st.slider("Assumed Annual Appreciation (%)", 0.0, 8.0, 3.0, step=0.5,
                              key="app_rate_slider") / 100
        selling_cost_pct = st.slider("Selling Costs (%)", 0.5, 3.0, 2.0, step=0.25,
                                      key="sell_cost_slider") / 100

    _purchase_costs = bsd + absd_net + legal_purchase + valuation_fee + renovation
    _cpf_rate_mo    = 0.025 / 12
    _cpf_lump       = cpf_oa_b1 + cpf_oa_b2
    _cpf_mo_usage   = cpf_b1*cpf_b1_pct/100 + cpf_b2*cpf_b2_pct/100

    def _cpf_refund(months):
        ci_lump = _cpf_lump * ((1+_cpf_rate_mo)**months - 1)
        ci_mo   = sum(_cpf_mo_usage * ((1+_cpf_rate_mo)**(months-j) - 1) for j in range(1, months+1))
        total   = _cpf_lump + _cpf_mo_usage*months
        return total + ci_lump + ci_mo

    exit_years = sorted(set([1,3,5,7,10,15,loan_tenor]))
    exit_rows  = []
    for ey in exit_years:
        if ey > loan_tenor: continue
        pv         = property_value * (1+app_rate)**ey
        net_sale   = pv * (1 - selling_cost_pct)
        m_idx      = min(ey*12-1, len(df_amort)-1)
        loan_bal   = df_amort["Balance"].iloc[m_idx]
        cpf_ref    = _cpf_refund(ey*12)
        cash_in_hand = net_sale - loan_bal - cpf_ref
        cum_cash_pmt = sum(cash_mtg_yr[:ey]) * 12
        total_cash_inv = down_payment + _purchase_costs + cum_cash_pmt
        net_gain   = cash_in_hand - total_cash_inv
        ann_ret    = (1 + net_gain/total_cash_inv)**(1/ey) - 1 if total_cash_inv>0 and ey>0 else 0
        exit_rows.append({
            "Exit Yr": ey,
            "Property Value": fmt(pv),
            "Loan Balance":   fmt(loan_bal),
            "Net Equity":     fmt(pv - loan_bal),
            "Cash Invested":  fmt(total_cash_inv),
            "CPF Refund":     fmt(cpf_ref),
            "Cash in Hand":   fmt(cash_in_hand),
            "Net Gain":       fmt(net_gain),
            "Ann. Return":    f"{ann_ret:.1%}" if total_cash_inv>0 else "—",
        })
    st.dataframe(pd.DataFrame(exit_rows), use_container_width=True, hide_index=True)

    with ea_chart:
        exit_yrs_plot = list(range(1, loan_tenor+1))
        for rate_plot, clr in [(0.00,"#aaa"),(0.02,"#e67e22"),(app_rate,"#1e7e5c"),(0.06,"#2980b9")]:
            label = f"{rate_plot:.0%} p.a.{' ← current' if rate_plot==app_rate else ''}"
            equities = [property_value*(1+rate_plot)**y -
                        df_amort["Balance"].iloc[min(y*12-1,len(df_amort)-1)]
                        for y in exit_yrs_plot]
            fig_ea = go.Figure() if rate_plot==0.00 else fig_ea
            fig_ea.add_trace(go.Scatter(x=exit_yrs_plot, y=equities, name=label, mode="lines",
                                         line=dict(color=clr, width=2.5 if rate_plot==app_rate else 1.5,
                                                   dash="solid" if rate_plot==app_rate else "dot")))
        cash_inv_line = [down_payment + _purchase_costs + sum(cash_mtg_yr[:y])*12
                         for y in exit_yrs_plot]
        fig_ea.add_trace(go.Scatter(x=exit_yrs_plot, y=cash_inv_line, name="Cash Invested",
                                     mode="lines", line=dict(color="#c0392b", width=2, dash="dash")))
        fig_ea.add_hline(y=0, line=dict(color="#999", width=0.8))
        fig_ea.update_layout(
            height=280, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
            font=dict(family="DM Sans", color="#0f1923"),
            title=dict(text="Net Equity at 0% / 2% / selected / 6% appreciation vs Cash Invested", font=dict(size=11)),
            legend=dict(orientation="h", y=-0.35, font=dict(size=10)),
            margin=dict(l=0, r=0, t=40, b=10),
            xaxis=dict(title="Year of Ownership", gridcolor="#e0dbd2", dtick=2),
            yaxis=dict(tickformat=",.0f", gridcolor="#e0dbd2", title="SGD"),
        )
        st.plotly_chart(fig_ea, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MORTGAGE ELIGIBILITY
# ══════════════════════════════════════════════════════════════════════════════
with tab_elig:
    st.markdown("### Mortgage Eligibility Assessment")
    st.caption("Private residential property · Bank loan · MAS regulations (indicative — confirm with your banker).")

    def elig_card(title, status, detail, kind="ok"):
        cls = {"ok":"ok-card","warn":"warn-card","err":"err-card","info":"info-card"}.get(kind,"ok-card")
        st.markdown(f'<div class="{cls}"><strong>{title}</strong> &nbsp;{status}<br>'
                    f'<span style="color:#555">{detail}</span></div>', unsafe_allow_html=True)

    # ── Section 1: Quick Eligibility Dashboard ────────────────────────────────
    st.markdown('<div class="section-label">Eligibility Summary</div>', unsafe_allow_html=True)
    ea,eb,ec,ed = st.columns(4)

    # LTV
    ltv_clr = "#1e7e5c" if ltv_ok else "#c0392b"
    ea.markdown(f"""<div class="kpi-card {'red' if not ltv_ok else ''}">
      <div class="kpi-label">LTV Ratio</div>
      <div class="kpi-value" style="color:{ltv_clr}">{ltv:.1%}</div>
      <div class="kpi-sub">Limit: {ltv_limit:.0%} {'⚠️ age-capped' if max_ltv_age_capped else '✅'}</div>
    </div>""", unsafe_allow_html=True)

    tdsr_clr = "#1e7e5c" if tdsr_stress_ok else "#c0392b"
    eb.markdown(f"""<div class="kpi-card {'red' if not tdsr_stress_ok else ''}">
      <div class="kpi-label">TDSR (stress @ 4%)</div>
      <div class="kpi-value" style="color:{tdsr_clr}">{tdsr_stress:.1f}%</div>
      <div class="kpi-sub">{'✅ Pass' if tdsr_stress_ok else '❌ Exceeds 55% limit'}</div>
    </div>""", unsafe_allow_html=True)

    cash_clr = "#1e7e5c" if min_cash_ok else "#c0392b"
    ec.markdown(f"""<div class="kpi-card {'red' if not min_cash_ok else ''}">
      <div class="kpi-label">5% Cash Minimum</div>
      <div class="kpi-value" style="color:{cash_clr}">{fmt(cash_only)}</div>
      <div class="kpi-sub">Required: {fmt(min_cash_req)} {'✅' if min_cash_ok else '❌'}</div>
    </div>""", unsafe_allow_html=True)

    overall_ok = ltv_ok and tdsr_stress_ok and min_cash_ok and tenure_ok
    ov_clr = "#1e7e5c" if overall_ok else "#c0392b"
    ov_txt = "Likely Eligible" if overall_ok else "Issues Found"
    ed.markdown(f"""<div class="kpi-card {'red' if not overall_ok else ''}">
      <div class="kpi-label">Overall Assessment</div>
      <div class="kpi-value" style="color:{ov_clr};font-size:1.4rem">{ov_txt}</div>
      <div class="kpi-sub">{'All checks passed' if overall_ok else 'See details below'}</div>
    </div>""", unsafe_allow_html=True)

    # ── Section 2: LTV & Age+Tenor Analysis ──────────────────────────────────
    st.markdown('<div class="section-label">LTV & Joint Borrower Age Analysis</div>', unsafe_allow_html=True)

    b1_at_maturity = b1_age + loan_tenor
    b2_at_maturity = b2_age + loan_tenor
    max_age_at_mat = max(b1_at_maturity, b2_at_maturity)

    age_col, ltv_col = st.columns(2)
    with age_col:
        elig_card("LTV Limit Check",
                  f"{'⚠️ 55% cap applies' if max_ltv_age_capped else '✅ 75% limit'}",
                  f"MAS applies the 55% LTV cap if: loan tenor > 30 years OR any borrower's age + tenor > 65. "
                  f"Your loan: {loan_tenor} yrs. "
                  f"B1 at maturity: {b1_at_maturity} | B2 at maturity: {b2_at_maturity}. "
                  f"{'Trigger: ' + ('Tenor > 30 yrs' if loan_tenor>30 else f'Oldest borrower {max_age_at_mat} at maturity > 65') if max_ltv_age_capped else 'No cap triggered.'}",
                  "warn" if max_ltv_age_capped and ltv_ok else ("err" if not ltv_ok else "ok"))

        # Optimal tenor table
        st.markdown("**Optimal tenor to stay within 75% LTV:**")
        rows_ten = []
        for ages in [(b1_age, b2_age)]:
            oldest = max(ages)
            max_t_age = max(0, 65 - oldest)
            max_t_reg = 30
            max_t_75  = min(max_t_age, max_t_reg)
            rows_ten.append({
                "Oldest Borrower Age": oldest,
                "Max Tenor for 75% LTV": f"{max_t_75} yrs" if max_t_75>0 else "Not available",
                "Your Tenor": f"{loan_tenor} yrs",
                "LTV Limit": f"{'75%' if loan_tenor<=max_t_75 and max_t_75>0 else '55%'}",
            })
        st.dataframe(pd.DataFrame(rows_ten), use_container_width=True, hide_index=True)

    with ltv_col:
        # LTV vs loan amount chart
        loan_range = np.arange(property_value*0.25, property_value*0.80, property_value*0.01)
        ltv_range  = loan_range / property_value
        fig_ltv = go.Figure()
        fig_ltv.add_trace(go.Scatter(x=loan_range, y=ltv_range*100, mode="lines",
                                      line=dict(color="#2980b9",width=2.5), fill="tozeroy",
                                      fillcolor="rgba(41,128,185,0.08)"))
        fig_ltv.add_hline(y=ltv_limit*100, line=dict(color="#c0392b",dash="dash",width=1.5),
                           annotation_text=f"Your LTV limit {ltv_limit:.0%}")
        fig_ltv.add_vline(x=loan_amount, line=dict(color="#1e7e5c",dash="dot",width=1.5),
                           annotation_text="Your loan")
        fig_ltv.update_layout(height=240, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                               font=dict(family="DM Sans",color="#0f1923"),
                               title="LTV vs Loan Amount", margin=dict(l=0,r=0,t=40,b=0),
                               xaxis=dict(tickformat=",.0f",title="Loan Amount"),
                               yaxis=dict(ticksuffix="%",title="LTV (%)"), showlegend=False)
        st.plotly_chart(fig_ltv, use_container_width=True)

    # ── Section 3: TDSR Deep Dive ─────────────────────────────────────────────
    st.markdown('<div class="section-label">TDSR Deep Dive</div>', unsafe_allow_html=True)
    td1, td2 = st.columns(2)

    with td1:
        st.markdown("**Recognised Income Breakdown (Year 1)**")
        rec_rows = [
            ("B1 Fixed (monthly)",       f"{fmt(f_b1_yr1/12)}"),
            (f"B1 Variable × {variable_haircut}% haircut", f"{fmt(rec_b1_yr1 - f_b1_yr1/12)}"),
            *([("B2 Fixed (monthly)", f"{fmt(f_b2_yr1/12)}"),
               (f"B2 Variable × {variable_haircut}% haircut", f"{fmt(rec_b2_yr1 - f_b2_yr1/12)}")] if include_b2 else []),
            ("Rental (recognised)",      f"{fmt(rental_rec)}"),
        ]
        for k,v in rec_rows:
            st.markdown(f'<div class="row-item"><span class="row-label">{k}</span><span>{v}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-total"><span>Total Recognised</span><span style="color:#2980b9">{fmt(total_rec_yr1)}/mo</span></div>', unsafe_allow_html=True)

        max_loan_55 = tdsr_max_loan(total_rec_yr1, existing_debt, loan_tenor, 0.55)
        max_loan_45 = tdsr_max_loan(total_rec_yr1, existing_debt, loan_tenor, 0.45)
        st.markdown("**Max Qualifying Loan @ 4% stress:**")
        st.markdown(f'<div class="row-item"><span class="row-label">At 55% TDSR</span><span style="color:#1e7e5c">{fmt(max_loan_55)}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-item"><span class="row-label">At 45% TDSR</span><span style="color:#e67e22">{fmt(max_loan_45)}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-item"><span class="row-label">Your loan</span><span style="color:#{"c0392b" if loan_amount>max_loan_55 else "0f1923"}">{fmt(loan_amount)}</span></div>', unsafe_allow_html=True)

    with td2:
        # TDSR sensitivity: income levels
        inc_levels = [15000,20000,25000,30000,35000,40000]
        tdsr_sens_rows = []
        for inc in inc_levels:
            ml = tdsr_max_loan(inc, existing_debt, loan_tenor)
            tdsr_sens_rows.append({
                "Gross Monthly": fmt(inc),
                "55% Cap/mo": fmt(inc*0.55),
                "Less Other Debt": fmt(existing_debt),
                "Avail for Mortgage": fmt(max(0, inc*0.55-existing_debt)),
                f"Max Loan ({loan_tenor}yr@4%)": fmt(ml),
                "Covers Yours?": "✅" if ml>=loan_amount else "❌",
            })
        st.dataframe(pd.DataFrame(tdsr_sens_rows), use_container_width=True, hide_index=True)

    # ── Section 4: CPF Usage Limits ───────────────────────────────────────────
    st.markdown('<div class="section-label">CPF Usage Limits for Private Property</div>', unsafe_allow_html=True)

    # Withdrawal limit based on tenure
    tenure_str = property_tenure
    if "Freehold" in tenure_str or "≥60yr" in tenure_str:
        cpf_wl_mult = 1.20; cpf_wl_note = "120% Valuation Limit applies (freehold / ≥60yr remaining lease)."
    elif "30–59yr" in tenure_str:
        cpf_wl_mult = 1.00; cpf_wl_note = "Basic Valuation Limit only (30–59yr remaining lease)."
    else:
        cpf_wl_mult = 0.00; cpf_wl_note = "CPF CANNOT be used: remaining lease < 30 years."

    valuation_limit     = property_value  # using purchase price as proxy
    withdrawal_limit    = round(valuation_limit * cpf_wl_mult)
    cpf_monthly_usage   = cpf_b1*cpf_b1_pct/100 + cpf_b2*cpf_b2_pct/100
    cpf_total_projected = cpf_monthly_usage * months_total + cpf_oa_b1 + cpf_oa_b2  # rough projection

    # Accrued interest on CPF used (2.5% p.a., compounded monthly)
    cpf_rate_mo = 0.025/12
    # If we use cpf_oa_b1+cpf_oa_b2 at start + cpf_monthly ongoing
    # Approximate accrued interest on total CPF used at end of loan
    cpf_lump    = cpf_oa_b1 + cpf_oa_b2
    cpf_acc_int = cpf_lump * ((1+cpf_rate_mo)**months_total - 1)
    for m in range(1, months_total+1):
        cpf_acc_int += cpf_monthly_usage * ((1+cpf_rate_mo)**(months_total-m+1) - 1)

    cl1, cl2 = st.columns(2)
    with cl1:
        elig_card("CPF Withdrawal Limit",
                  f"{'✅' if cpf_wl_mult>0 else '❌'} {tenure_str}",
                  cpf_wl_note, "ok" if cpf_wl_mult>=1.2 else ("warn" if cpf_wl_mult>0 else "err"))
        st.markdown(f"""
| Item | Amount |
|---|---|
| Valuation Limit | {fmt(valuation_limit)} |
| Withdrawal Limit ({cpf_wl_mult:.0%} VL) | {fmt(withdrawal_limit)} |
| Projected CPF used (incl. OA balance) | {fmt(cpf_total_projected)} |
| Within withdrawal limit? | {'✅ Yes' if cpf_total_projected<=withdrawal_limit else '⚠️ May exceed — check with CPF Board'} |
""")

    with cl2:
        st.markdown("**CPF Refund on Sale (Accrued Interest)**")
        st.caption("When you sell, CPF + 2.5% p.a. accrued interest must be refunded to your OA. "
                   "This reduces your net sale proceeds but the funds return to CPF for future use.")
        ai_rows = []
        for yrs in [5,10,15,20,loan_tenor]:
            m = yrs*12
            ci_lump = cpf_lump * ((1+cpf_rate_mo)**m - 1)
            ci_mo   = sum(cpf_monthly_usage * ((1+cpf_rate_mo)**(m-j) - 1) for j in range(1,m+1))
            total_cpf_used = cpf_lump + cpf_monthly_usage*m
            total_with_int = total_cpf_used + ci_lump + ci_mo
            ai_rows.append({"Hold (yrs)":yrs,
                             "CPF Used": fmt(total_cpf_used),
                             "Accrued Interest": fmt(ci_lump+ci_mo),
                             "Total to Refund": fmt(total_with_int)})
        st.dataframe(pd.DataFrame(ai_rows), use_container_width=True, hide_index=True)

    # ── Section 5: How Much Can I Borrow ─────────────────────────────────────
    st.markdown('<div class="section-label">How Much Can I Borrow?</div>', unsafe_allow_html=True)
    borrow_col, borrow_chart = st.columns([1,2])
    with borrow_col:
        tdsr_target = st.slider("Target TDSR (%)", 30, 55, 50, key="tdsr_target_slider")
        max_borrow  = tdsr_max_loan(total_rec_yr1, existing_debt, loan_tenor, tdsr_target/100)
        max_pv_75   = max_borrow / (1 - 0.75) if (1-0.75)>0 else 0  # max property at 75% LTV
        max_pv_55   = max_borrow / (1 - 0.55) if (1-0.55)>0 else 0
        max_pv_applicable = max_pv_55 if max_ltv_age_capped else max_pv_75
        st.markdown(f"""
| Metric | Value |
|---|---|
| Max Loan @ {tdsr_target}% TDSR | **{fmt(max_borrow)}** |
| Equivalent Max Property ({ltv_limit:.0%} LTV) | **{fmt(max_pv_applicable)}** |
| Your Loan | {fmt(loan_amount)} |
| Headroom | **{fmt(max_borrow - loan_amount)}** |
""")
    with borrow_chart:
        tdsr_pcts  = list(range(30, 57, 5))
        max_loans  = [tdsr_max_loan(total_rec_yr1, existing_debt, loan_tenor, t/100) for t in tdsr_pcts]
        fig_borrow = go.Figure()
        fig_borrow.add_trace(go.Bar(x=[f"{t}%" for t in tdsr_pcts], y=max_loans,
                                     marker_color=["#c0392b" if t>55 else ("#e67e22" if t>45 else "#1e7e5c") for t in tdsr_pcts],
                                     text=[fmt(v) for v in max_loans], textposition="auto"))
        fig_borrow.add_hline(y=loan_amount, line=dict(color="#2980b9",dash="dash",width=1.5),
                              annotation_text="Your loan")
        fig_borrow.update_layout(height=260, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                                  font=dict(family="DM Sans",color="#0f1923"),
                                  title="Max Qualifying Loan by TDSR Target", showlegend=False,
                                  margin=dict(l=0,r=0,t=40,b=0),
                                  xaxis_title="TDSR Target", yaxis=dict(tickformat=",.0f"))
        st.plotly_chart(fig_borrow, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REGULATORY CHECKS
# ══════════════════════════════════════════════════════════════════════════════
with tab_reg:
    st.markdown("### Regulatory & Affordability Checks")
    st.caption("Indicative only — confirm with your bank and lawyer before committing.")

    def reg_card(title, status, detail, kind="ok"):
        cls = {"ok":"ok-card","warn":"warn-card","err":"err-card"}.get(kind,"ok-card")
        st.markdown(f'<div class="{cls}"><strong>{title}</strong> &nbsp;{status}<br>'
                    f'<span style="color:#555">{detail}</span></div>', unsafe_allow_html=True)

    reg_card("LTV Ratio",
             "✅ Pass" if ltv_ok else "❌ Fail",
             f"Your LTV: {ltv:.1%} | Applicable limit: {ltv_limit:.0%} "
             f"({'age/tenor cap triggered — 55%' if max_ltv_age_capped else '75% standard'}). "
             f"Loan {fmt(loan_amount)} vs property {fmt(property_value)}.",
             "ok" if ltv_ok else "err")

    reg_card("5% Minimum Cash Downpayment",
             "✅ Pass" if min_cash_ok else "❌ Fail",
             f"5% of purchase price = {fmt(min_cash_req)} must be cash (CPF cannot count). "
             f"Your cash (B1+B2, ex-CPF): {fmt(cash_only)}.",
             "ok" if min_cash_ok else "err")

    reg_card(f"TDSR (stress-tested @ {STRESS:.0%})",
             "✅ Pass" if tdsr_stress_ok else "❌ Fail",
             f"Stress TDSR: {tdsr_stress:.1f}% (limit 55%). "
             f"Stress monthly payment: {fmt(stress_pmt)}. "
             f"Max qualifying loan @ 4% / {loan_tenor}yr: {fmt(tdsr_max_loan(total_rec_yr1,existing_debt,loan_tenor))}.",
             "ok" if tdsr_stress_ok else "err")

    reg_card("Loan Tenure",
             "✅ Within limit" if tenure_ok else "❌ Exceeds limit",
             f"Max tenure: 35 years. Yours: {loan_tenor} yrs. "
             f"Note: B1 age at maturity = {b1_at_maturity}, B2 age at maturity = {b2_at_maturity}. "
             f"If {'any' if max_ltv_age_capped else 'no'} borrower exceeds age 65 at maturity, 55% LTV applies.",
             "ok" if tenure_ok else "err")

    if ssd > 0:
        reg_card("SSD — Property Sale",
                 "⚠️ SSD Applies",
                 f"Held {sale_held_yrs:.1f} yrs → SSD: {fmt(ssd)}. "
                 f"Net proceeds: {fmt(sale_proceeds)}.",
                 "warn")
    else:
        reg_card("SSD — Property Sale", "✅ No SSD",
                 f"Held {sale_held_yrs:.1f} yrs — beyond 3-year SSD window.", "ok")

    if absd_rate == 0:
        reg_card("ABSD", "✅ No ABSD", "First property for SC — 0% ABSD.", "ok")
    elif absd_remission:
        reg_card("ABSD — Remission Pathway",
                 "⚠️ Upfront then refunded",
                 f"ABSD upfront: {fmt(absd)} ({absd_rate:.0%}). "
                 f"Refundable if existing property sold within 6 months of new completion. "
                 f"Ensure {fmt(absd)} available at exercise/BSD stage.",
                 "warn")
    else:
        reg_card("ABSD", "❌ ABSD Due (non-refundable)",
                 f"ABSD: {fmt(absd)} ({absd_rate:.0%}) — adds to total cost.", "err")

    reg_card("BSD (Feb 2023 rates — 6 brackets)",
             "ℹ️ Calculated",
             f"BSD on {fmt(property_value)} = {fmt(bsd)} ({bsd/property_value:.2%} effective). "
             f"6% bracket applies to {fmt(max(0,property_value-3_000_000))} above SGD 3M.",
             "ok")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CASH TIMELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab_tl:
    scen = st.radio("Scenario", ["Scenario 1 — 1% OTP + 4% Exercise (~2 wks)",
                                  "Scenario 2 — 4% OTP + 1% Exercise (~12 wks)"],
                    horizontal=True)
    df_tl = df_s1 if "1" in scen.split("—")[0] else df_s2

    STAGE_COLORS = {"Starting Cash":"#1e7e5c","OTP":"#c0392b","House Sale":"#1e7e5c",
                    "Exercise":"#c0392b","Completion":"#c0392b",
                    "ABSD Refund":"#1e7e5c","Post-Completion":"#e67e22"}

    fig_tl = go.Figure()
    fig_tl.add_trace(go.Scatter(
        x=df_tl["Date"].astype(str), y=df_tl["Cum"],
        mode="lines+markers",
        line=dict(color="#2980b9",width=2),
        marker=dict(size=9, color=[STAGE_COLORS.get(s,"#7a9bb5") for s in df_tl["Stage"]]),
        hovertemplate="<b>%{text}</b><br>S$%{y:,.0f}<extra></extra>",
        text=df_tl["Desc"]))
    fig_tl.add_hline(y=0, line=dict(color="#c0392b",dash="dash",width=1.2),
                     annotation_text="Zero cash")
    fig_tl.update_layout(title="Cumulative Cash Position",
                          paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                          font=dict(family="DM Sans",color="#0f1923"),
                          height=360, margin=dict(l=0,r=0,t=40,b=10),
                          xaxis_title="Date", yaxis=dict(tickformat=",.0f",title="SGD"))
    st.plotly_chart(fig_tl, use_container_width=True)

    disp = df_tl.copy()
    disp["Date"] = pd.to_datetime(disp["Date"]).dt.strftime("%d %b %Y")
    for c in ["In","Out","Cum"]:
        disp[c] = disp[c].apply(lambda x: fmt(x) if x!=0 else "—")
    st.dataframe(disp[["Stage","Date","Desc","In","Out","Cum"]].rename(columns={
        "Desc":"Description","In":"Cash In","Out":"Cash Out","Cum":"Cumulative"}),
        use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — AFFORDABILITY & CASHFLOW
# ══════════════════════════════════════════════════════════════════════════════
with tab_aff:
    st.markdown('<div class="section-label">Joint Income Progression vs Mortgage Burden</div>', unsafe_allow_html=True)

    fig_inc = make_subplots(specs=[[{"secondary_y":True}]])
    fig_inc.add_trace(go.Bar(x=years, y=rec_b1_yr, name="B1 (recognised)", marker_color="#1e7e5c", opacity=0.9), secondary_y=False)
    if include_b2:
        fig_inc.add_trace(go.Bar(x=years, y=rec_b2_yr, name="B2 (recognised)", marker_color="#2980b9", opacity=0.9), secondary_y=False)
    fig_inc.add_trace(go.Scatter(x=years, y=pmt_by_yr, name="Monthly Mortgage",
                                  line=dict(color="#c0392b",width=2.5,dash="dash"), mode="lines"), secondary_y=False)
    fig_inc.add_trace(go.Scatter(x=years, y=tdsr_yr, name="TDSR (%)",
                                  line=dict(color="#e67e22",width=2.5), mode="lines+markers",
                                  marker=dict(size=5)), secondary_y=True)
    fig_inc.add_hline(y=55, line=dict(color="#c0392b",dash="dot",width=1.2),
                      annotation_text="55% TDSR Limit", secondary_y=True, annotation_position="top right")
    for i in range(1, num_periods):
        fig_inc.add_vline(x=i*5+0.5, line=dict(color="#aaa",dash="dot",width=1))
    fig_inc.update_layout(barmode="stack", height=340, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                           font=dict(family="DM Sans",color="#0f1923"),
                           legend=dict(orientation="h",y=-0.22), margin=dict(l=0,r=0,t=10,b=10),
                           xaxis=dict(title="Year of Loan",gridcolor="#e0dbd2",dtick=1))
    fig_inc.update_yaxes(title_text="Monthly SGD", secondary_y=False, tickformat=",.0f", gridcolor="#e0dbd2")
    fig_inc.update_yaxes(title_text="TDSR (%)", secondary_y=True, tickformat=".0f", ticksuffix="%", showgrid=False)
    st.plotly_chart(fig_inc, use_container_width=True)

    # Cashflow table per year
    cf_rows = []
    for i,y in enumerate(years):
        pb1 = periods_b1[period_idx(y,num_periods)]; pb2 = periods_b2[period_idx(y,num_periods)]
        tx1 = compute_tax(pb1["fixed"],pb1["fixed"]*pb1["var_pct"]/100,b1_age+(y-1),num_children,spouse_work)
        tx2 = compute_tax(pb2["fixed"],pb2["fixed"]*pb2["var_pct"]/100,b2_age+(y-1),b2_num_children,b2_spouse_work)
        g1_mo = tx1["Gross"]/12; g2_mo = tx2["Gross"]/12
        t1_mo = tx1["Tax Payable"]/12; t2_mo = tx2["Tax Payable"]/12
        c1_mo = tx1["CPF_EE"]/12;      c2_mo = tx2["CPF_EE"]/12
        n1_mo = g1_mo-t1_mo-c1_mo;    n2_mo = g2_mo-t2_mo-c2_mo
        net_tot = n1_mo+n2_mo
        cm = cash_mtg_yr[i]; surp = surplus_by_yr[i]
        cf_rows.append({
            "Year":y,"Gross (Joint)":g1_mo+g2_mo,"Tax (Joint)":t1_mo+t2_mo,
            "CPF (Joint)":c1_mo+c2_mo,"Net Take-Home":net_tot,
            "Cash Mortgage":cm,"Mortgage %":cm/net_tot*100 if net_tot>0 else 0,
            "Total Expenses":total_exp+existing_debt,"Surplus":surp,
            "Surplus %":surp/net_tot*100 if net_tot>0 else 0,
        })
    df_cf = pd.DataFrame(cf_rows)

    cf_l, cf_r = st.columns([1,2])
    with cf_l:
        yr1r = cf_rows[0]
        d_labels = ["Income Tax","CPF (Employee)","Cash Mortgage",
                    "Food","Transport","Utilities","Insurance",
                    "Childcare","Lifestyle","Travel","Family","Other","Debt","Surplus"]
        d_values = [yr1r["Tax (Joint)"],yr1r["CPF (Joint)"],yr1r["Cash Mortgage"],
                    exp_food,exp_transport,exp_utilities,exp_insurance,
                    exp_childcare,exp_lifestyle,exp_travel,exp_family,exp_other,
                    existing_debt, max(yr1r["Surplus"],0)]
        d_colors = ["#922b21","#1a5276","#c0392b",
                    "#1e7e5c","#2980b9","#8e44ad","#e67e22",
                    "#16a085","#d35400","#2c3e50","#7f8c8d","#95a5a6",
                    "#bdc3c7","#27ae60"]
        filt = [(l,v,c) for l,v,c in zip(d_labels,d_values,d_colors) if v>0]
        fl,fv,fc = zip(*filt) if filt else ([],[],[])
        fig_donut = go.Figure(go.Pie(
            labels=fl, values=fv, hole=0.52,
            marker=dict(colors=fc,line=dict(color="#f7f4ef",width=2)),
            textinfo="percent", sort=False,
            hovertemplate="<b>%{label}</b><br>S$%{value:,.0f}/mo<extra></extra>"))
        fig_donut.update_layout(
            height=340, paper_bgcolor="#f7f4ef",
            font=dict(family="DM Sans",color="#0f1923",size=11),
            title=dict(text="Yr 1 Gross Allocation",font=dict(size=12)),
            legend=dict(orientation="v",x=1.02,y=0.5,font=dict(size=9)),
            margin=dict(l=0,r=120,t=40,b=0),
            annotations=[dict(text=f"<b>{fmt(yr1r['Gross (Joint)'])}</b><br>gross/mo",
                              x=0.5,y=0.5,showarrow=False,font=dict(size=11,color="#0f1923"),xanchor="center")])
        st.plotly_chart(fig_donut, use_container_width=True)

    with cf_r:
        fig_stack = go.Figure()
        fig_stack.add_trace(go.Scatter(x=years, y=[r["Gross (Joint)"] for r in cf_rows],
                                        name="Gross Income", mode="lines",
                                        line=dict(color="#0f1923",width=2,dash="dot")))
        stack_layers = [
            ("Income Tax",          [r["Tax (Joint)"]  for r in cf_rows], "#922b21"),
            ("CPF (Employee)",      [r["CPF (Joint)"]  for r in cf_rows], "#1a5276"),
            ("Cash Mortgage",       cash_mtg_yr,                          "#c0392b"),
            ("Food",                [exp_food]*loan_tenor,                "#1e7e5c"),
            ("Transport",           [exp_transport]*loan_tenor,           "#2980b9"),
            ("Utilities",           [exp_utilities]*loan_tenor,           "#8e44ad"),
            ("Insurance",           [exp_insurance]*loan_tenor,           "#e67e22"),
            ("Childcare",           [exp_childcare]*loan_tenor,           "#16a085"),
            ("Lifestyle",           [exp_lifestyle]*loan_tenor,           "#d35400"),
            ("Travel",              [exp_travel]*loan_tenor,              "#2c3e50"),
            ("Family Support",      [exp_family]*loan_tenor,              "#7f8c8d"),
            ("Other",               [exp_other]*loan_tenor,               "#95a5a6"),
            ("Debt",                [existing_debt]*loan_tenor,           "#bdc3c7"),
        ]
        for name,vals,color in stack_layers:
            if all(v==0 for v in vals): continue
            fig_stack.add_trace(go.Bar(x=years,y=vals,name=name,marker_color=color,opacity=0.88))
        sc_colors = ["#c0392b" if s<0 else "#27ae60" for s in surplus_by_yr]
        fig_stack.add_trace(go.Scatter(x=years,y=surplus_by_yr,name="Surplus",mode="lines+markers",
                                        line=dict(color="#27ae60",width=2.5),
                                        marker=dict(size=7,color=sc_colors,line=dict(color="#fff",width=1.5))))
        fig_stack.add_hline(y=0,line=dict(color="#c0392b",width=1,dash="dash"))
        for i in range(1,num_periods):
            fig_stack.add_vline(x=i*5+0.5,line=dict(color="#aaa",dash="dot",width=1))
        fig_stack.update_layout(barmode="stack",height=340,paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                                 font=dict(family="DM Sans",color="#0f1923"),
                                 legend=dict(orientation="h",y=-0.3,font=dict(size=10)),
                                 margin=dict(l=0,r=0,t=40,b=10),
                                 title=dict(text="Monthly Gross-to-Surplus Waterfall",font=dict(size=12)),
                                 xaxis=dict(title="Year",gridcolor="#e0dbd2",dtick=1),
                                 yaxis=dict(tickformat=",.0f",gridcolor="#e0dbd2",title="SGD/mo"))
        st.plotly_chart(fig_stack, use_container_width=True)

    # Surplus & mortgage burden charts
    s_l, s_r = st.columns(2)
    with s_l:
        s_clrs = ["#c0392b" if s<0 else "#1e7e5c" for s in surplus_by_yr]
        fig_surp = make_subplots(specs=[[{"secondary_y":True}]])
        fig_surp.add_trace(go.Bar(x=years,y=surplus_by_yr,name="Monthly Surplus",
                                   marker_color=s_clrs,opacity=0.85), secondary_y=False)
        fig_surp.add_trace(go.Scatter(x=years,y=[r["Surplus %"] for r in cf_rows],name="Surplus %",
                                       mode="lines+markers",line=dict(color="#8e44ad",width=2),
                                       marker=dict(size=5)), secondary_y=True)
        fig_surp.add_hline(y=0,line=dict(color="#0f1923",width=1.2))
        fig_surp.update_layout(height=280,paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                                font=dict(family="DM Sans",color="#0f1923"),
                                title=dict(text="Monthly Surplus & Surplus Rate",font=dict(size=12)),
                                legend=dict(orientation="h",y=-0.3),margin=dict(l=0,r=0,t=40,b=10),
                                xaxis=dict(title="Year",gridcolor="#e0dbd2",dtick=1))
        fig_surp.update_yaxes(title_text="SGD/mo",secondary_y=False,tickformat=",.0f",gridcolor="#e0dbd2")
        fig_surp.update_yaxes(title_text="Surplus %",secondary_y=True,tickformat=".0f",ticksuffix="%",showgrid=False)
        st.plotly_chart(fig_surp, use_container_width=True)

    with s_r:
        fig_burden = go.Figure()
        fig_burden.add_trace(go.Scatter(x=years,y=[r["Mortgage %"] for r in cf_rows],
                                         mode="lines+markers",fill="tozeroy",
                                         line=dict(color="#c0392b",width=2.5),
                                         fillcolor="rgba(192,57,43,0.08)",marker=dict(size=5)))
        fig_burden.add_hline(y=30,line=dict(color="#e67e22",dash="dash",width=1.5),
                              annotation_text="30% guideline",annotation_position="top right")
        fig_burden.update_layout(height=280,paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                                  font=dict(family="DM Sans",color="#0f1923"),
                                  title=dict(text="Cash Mortgage as % of Joint Net Take-Home",font=dict(size=12)),
                                  margin=dict(l=0,r=0,t=40,b=10),showlegend=False,
                                  xaxis=dict(title="Year",gridcolor="#e0dbd2",dtick=1),
                                  yaxis=dict(tickformat=".0f",ticksuffix="%",gridcolor="#e0dbd2"))
        st.plotly_chart(fig_burden, use_container_width=True)

    st.markdown("**Annual Cashflow Summary**")
    cf_disp = df_cf[["Year","Gross (Joint)","Tax (Joint)","CPF (Joint)","Net Take-Home",
                      "Cash Mortgage","Mortgage %","Total Expenses","Surplus","Surplus %"]].copy()
    for c in ["Gross (Joint)","Tax (Joint)","CPF (Joint)","Net Take-Home","Cash Mortgage","Total Expenses","Surplus"]:
        cf_disp[c] = cf_disp[c].map(lambda x: f"{x:,.0f}")
    for c in ["Mortgage %","Surplus %"]:
        cf_disp[c] = cf_disp[c].map(lambda x: f"{x:.1f}%")
    st.caption("All values monthly (SGD). Surplus = Net Take-Home − Cash Mortgage − Total Expenses.")
    st.dataframe(cf_disp, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — TAX ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_tax:
    st.markdown('<div class="section-label">Singapore Income Tax Estimate — YA2024 Basis</div>', unsafe_allow_html=True)

    _borrowers = [("Borrower 1", periods_b1, b1_age, num_children, spouse_work, "tag-b1")]
    if include_b2:
        _borrowers.append(("Borrower 2", periods_b2, b2_age, b2_num_children, b2_spouse_work, "tag-b2"))
    for borrower_label, periods_bx, bx_age, nc, spw, tag_class in _borrowers:
        st.markdown(f'<span class="borrower-tag {tag_class}">{borrower_label}</span>', unsafe_allow_html=True)
        t1, t2, t3 = st.columns(3)
        fp0 = periods_bx[0]["fixed"]; vp0 = fp0*periods_bx[0]["var_pct"]/100
        tx0 = compute_tax(fp0, vp0, bx_age, nc, spw)
        with t1:
            st.markdown("**Year-1 Tax Detail**")
            for k,v in [("Gross Income",tx0["Gross"]),("CPF (Employee)",tx0["CPF_EE"]),
                         ("Total Reliefs",tx0["Total Relief"]),("Chargeable Income",tx0["Chargeable"]),
                         ("Tax Before Rebate",tx0["Tax Before Rebate"]),("PTR (annualised)",tx0["PTR"]),
                         ("Tax Payable",tx0["Tax Payable"])]:
                st.write(f"{k}: **{fmt(v)}**")
            st.markdown(f"Effective Rate: **{tx0['Eff Rate']:.1f}%**")
        with t2:
            st.markdown("**Relief Breakdown**")
            for k,v in tx0["reliefs"].items():
                st.write(f"{k}: **{fmt(v)}**")
            st.markdown("---")
            st.caption("SG-sourced employment income. CPF Relief = employee contribution. PTR spread ~5 yrs.")
        with t3:
            st.markdown("**Tax by Period**")
            tax_tbl = []
            for i,p in enumerate(periods_bx):
                vp = p["fixed"]*p["var_pct"]/100
                ai = bx_age + i*5
                tx = compute_tax(p["fixed"], vp, ai, nc, spw)
                tax_tbl.append({"Period":period_labels[i],
                                 "Gross p.a.":f"SGD {tx['Gross']:,.0f}",
                                 "Tax Payable":f"SGD {tx['Tax Payable']:,.0f}",
                                 "Eff Rate":f"{tx['Eff Rate']:.1f}%",
                                 "Monthly Tax":f"SGD {tx['Tax Payable']/12:,.0f}"})
            st.dataframe(pd.DataFrame(tax_tbl), use_container_width=True, hide_index=True)

            tax_v=[]; cpf_v=[]; net_v=[]; lbl_v=[]
            for i,p in enumerate(periods_bx):
                vp = p["fixed"]*p["var_pct"]/100; ai = bx_age+i*5
                tx = compute_tax(p["fixed"],vp,ai, nc, spw)
                tax_v.append(tx["Tax Payable"]/12); cpf_v.append(tx["CPF_EE"]/12)
                net_v.append((tx["Gross"]-tx["Tax Payable"]-tx["CPF_EE"])/12)
                lbl_v.append(period_labels[i])
            fig_tax = go.Figure()
            fig_tax.add_trace(go.Bar(name="Net",x=lbl_v,y=net_v,marker_color="#1e7e5c"))
            fig_tax.add_trace(go.Bar(name="CPF",x=lbl_v,y=cpf_v,marker_color="#2980b9"))
            fig_tax.add_trace(go.Bar(name="Tax",x=lbl_v,y=tax_v,marker_color="#c0392b"))
            fig_tax.update_layout(barmode="stack",height=200,paper_bgcolor="#f7f4ef",
                                   plot_bgcolor="#f7f4ef",font=dict(family="DM Sans",color="#0f1923",size=10),
                                   legend=dict(orientation="h",y=-0.4),margin=dict(l=0,r=0,t=10,b=0),
                                   yaxis=dict(tickformat=",.0f",gridcolor="#e0dbd2"))
            st.plotly_chart(fig_tax, use_container_width=True)
        st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — LOAN SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
with tab_loan:
    # Amortisation chart (variable-rate from dynamic model)
    st.markdown('<div class="section-label">Variable-Rate Amortisation</div>', unsafe_allow_html=True)
    df_yr_am = df_amort.groupby("Year").agg(
        Principal=("Principal","sum"), Interest=("Interest","sum"), Balance=("Balance","last")).reset_index()
    fig_am = make_subplots(specs=[[{"secondary_y":True}]])
    fig_am.add_trace(go.Bar(x=df_yr_am["Year"],y=df_yr_am["Principal"],name="Principal",marker_color="#1e7e5c"), secondary_y=False)
    fig_am.add_trace(go.Bar(x=df_yr_am["Year"],y=df_yr_am["Interest"],name="Interest",marker_color="#e8c99a"), secondary_y=False)
    fig_am.add_trace(go.Scatter(x=df_yr_am["Year"],y=df_yr_am["Balance"],name="Balance",
                                 line=dict(color="#c0392b",width=2.5),mode="lines"), secondary_y=True)
    fig_am.update_layout(barmode="stack",height=280,paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                          font=dict(family="DM Sans",color="#0f1923"),
                          legend=dict(orientation="h",y=-0.3),margin=dict(l=0,r=0,t=10,b=10))
    fig_am.update_yaxes(title_text="Annual Payment",secondary_y=False,tickformat=",.0f",gridcolor="#e0dbd2")
    fig_am.update_yaxes(title_text="Balance",secondary_y=True,tickformat=",.0f",showgrid=False)
    st.plotly_chart(fig_am, use_container_width=True)

    # Loan schedule metrics
    ls1,ls2,ls3,ls4 = st.columns(4)
    ls1.metric("Monthly Payment (Yr 1)", fmt(pmt_yr1))
    ls2.metric("Total Interest (var rate)", fmt(total_interest))
    ls3.metric("Total Interest (fixed)", fmt(int_sched))
    ls4.metric("Loan End", df_loan["Date"].iloc[-1].strftime("%b %Y"))

    # Fixed-rate schedule charts
    st.markdown('<div class="section-label">Fixed-Rate Schedule (Yr-1 rate)</div>', unsafe_allow_html=True)
    fig_lp = go.Figure()
    fig_lp.add_trace(go.Scatter(x=df_loan["Date"].astype(str),y=df_loan["Principal"],
                                 name="Principal",fill="tozeroy",line=dict(color="#2980b9"),stackgroup="one"))
    fig_lp.add_trace(go.Scatter(x=df_loan["Date"].astype(str),y=df_loan["Interest"],
                                 name="Interest",fill="tonexty",line=dict(color="#c0392b"),stackgroup="one"))
    fig_lp.update_layout(title="Monthly Principal vs Interest",paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                          font=dict(family="DM Sans",color="#0f1923"),height=260,margin=dict(l=0,r=0,t=40,b=10))
    st.plotly_chart(fig_lp, use_container_width=True)

    # Monthly schedule views
    view = st.radio("", ["First 24 months","By Year","Full Schedule"], horizontal=True, label_visibility="collapsed")
    if view=="By Year":
        df_yr_disp = df_loan.copy(); df_yr_disp["Year"]=pd.to_datetime(df_yr_disp["Date"]).dt.year
        yr_sum = df_yr_disp.groupby("Year").agg(Principal=("Principal","sum"),Interest=("Interest","sum"),Balance=("End Balance","last")).reset_index()
        for c in ["Principal","Interest","Balance"]: yr_sum[c] = yr_sum[c].apply(lambda x: fmt(x))
        st.dataframe(yr_sum, use_container_width=True, hide_index=True)
    else:
        d = df_loan.head(24) if view=="First 24 months" else df_loan
        d2 = d[["#","Date","Beg Balance","Payment","Principal","Interest","End Balance","Cum Interest"]].copy()
        d2["Date"] = pd.to_datetime(d2["Date"]).dt.strftime("%b %Y")
        for c in ["Beg Balance","Payment","Principal","Interest","End Balance","Cum Interest"]:
            d2[c] = d2[c].apply(lambda x: fmt(x))
        st.dataframe(d2, use_container_width=True, hide_index=True, height=400)

    # Dynamic schedule view
    st.markdown('<div class="section-label">Variable-Rate Monthly Schedule</div>', unsafe_allow_html=True)
    dv = st.radio("View", ["First 24 months","By Year (summary)","Full"], horizontal=True,
                   label_visibility="collapsed", key="dyn_view")
    if dv=="By Year (summary)":
        df_dy = df_amort.groupby("Year").agg(
            Rate=("Rate","first"),Payment=("Payment","sum"),
            Principal=("Principal","sum"),Interest=("Interest","sum"),
            Balance=("Balance","last"),TDSR=("TDSR","mean"),Surplus=("Surplus","mean")).reset_index()
        df_dy["Rate"]=df_dy["Rate"].map(lambda x:f"{x:.2f}%")
        df_dy["TDSR"]=df_dy["TDSR"].map(lambda x:f"{x:.1f}%")
        for c in ["Payment","Principal","Interest","Balance","Surplus"]:
            df_dy[c]=df_dy[c].map(lambda x:fmt(x))
        st.dataframe(df_dy, use_container_width=True, hide_index=True)
    else:
        ds = df_amort.head(24) if dv=="First 24 months" else df_amort
        ds2 = ds[["Month","Year","Rate","Payment","Principal","Interest","Balance","TDSR","Cash Mortgage","Surplus"]].copy()
        ds2["Rate"]=ds2["Rate"].map(lambda x:f"{x:.2f}%")
        ds2["TDSR"]=ds2["TDSR"].map(lambda x:f"{x:.1f}%")
        for c in ["Payment","Principal","Interest","Balance","Cash Mortgage","Surplus"]:
            ds2[c]=ds2[c].map(lambda x:fmt(x))
        st.dataframe(ds2, use_container_width=True, hide_index=True, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — STAMP DUTY
# ══════════════════════════════════════════════════════════════════════════════
with tab_sd:
    st.markdown("### Stamp Duty Breakdown")
    st.caption("BSD: IRAS rates effective 15 Feb 2023 | ABSD: effective 27 Apr 2023")

    sd1,sd2 = st.columns(2)
    with sd1:
        st.markdown("**Buyer's Stamp Duty (BSD) — 6 Brackets**")
        bsd_detail = [
            ("First S$180,000",  0.01, min(property_value,180_000)),
            ("Next S$180,000",   0.02, max(0,min(property_value-180_000,180_000))),
            ("Next S$640,000",   0.03, max(0,min(property_value-360_000,640_000))),
            ("Next S$500,000",   0.04, max(0,min(property_value-1_000_000,500_000))),
            ("Next S$1,500,000", 0.05, max(0,min(property_value-1_500_000,1_500_000))),
            ("Above S$3,000,000",0.06, max(0,property_value-3_000_000)),
        ]
        bsd_rows=[{"Bracket":b,"Rate":f"{r:.0%}","Taxable":fmt(t),"BSD":fmt(round(t*r))}
                  for b,r,t in bsd_detail]
        st.dataframe(pd.DataFrame(bsd_rows), use_container_width=True, hide_index=True)
        st.markdown(f"**Total BSD: {fmt(bsd)}** | Effective: {bsd/property_value:.2%}")

    with sd2:
        st.markdown("**ABSD & Total Stamp Duty**")
        for label,val in [("BSD",fmt(bsd)),(f"ABSD ({absd_rate:.0%})",fmt(absd)),
                           ("Remission?","Yes — refundable" if (absd_remission and absd>0) else "No"),
                           ("Net ABSD",fmt(absd_net)),
                           ("Total Stamp Duty",fmt(stamp_total)),
                           ("Effective Rate",f"{stamp_total/property_value:.2%}")]:
            st.markdown(f'<div class="row-item"><span class="row-label">{label}</span><span>{val}</span></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**ABSD Quick Reference (2025)**")
        absd_ref = pd.DataFrame([
            ("SC","1st","0%"),("SC","2nd","20%"),("SC","3rd+","30%"),
            ("SPR","1st","5%"),("SPR","2nd+","25%"),
            ("Foreigner","Any","60%"),("Entity/Trust","Any","65%"),
        ], columns=["Profile","Property Count","ABSD"])
        st.dataframe(absd_ref, use_container_width=True, hide_index=True)

    prices   = list(range(500_000, 10_000_001, 100_000))
    bsds_s   = [calc_bsd(p) for p in prices]
    eff_r    = [b/p*100 for b,p in zip(bsds_s,prices)]
    fig_bsd  = go.Figure()
    fig_bsd.add_trace(go.Bar(x=prices,y=bsds_s,name="BSD",marker_color="#2980b9",yaxis="y"))
    fig_bsd.add_trace(go.Scatter(x=prices,y=eff_r,name="Effective Rate (%)",
                                  line=dict(color="#c0392b",width=2),yaxis="y2"))
    fig_bsd.add_vline(x=property_value,line_dash="dash",line_color="#1e7e5c",annotation_text=f"{fmt(property_value)}")
    fig_bsd.update_layout(
        title="BSD vs Property Price",paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
        font=dict(family="DM Sans",color="#0f1923"),height=360,margin=dict(l=0,r=0,t=40,b=10),
        xaxis=dict(title="Price",tickformat=",.0f"),
        yaxis=dict(title="BSD",tickformat=",.0f"),
        yaxis2=dict(title="Effective Rate (%)",overlaying="y",side="right",tickformat=".2f"),
        legend=dict(x=0.02,y=0.98))
    st.plotly_chart(fig_bsd, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 — SENSITIVITY
# ══════════════════════════════════════════════════════════════════════════════
with tab_sens:
    st.markdown('<div class="section-label">Sensitivity Analysis</div>', unsafe_allow_html=True)
    ss1,ss2 = st.columns(2)

    with ss1:
        rates_s  = np.arange(1.5, 6.1, 0.5)
        tenors_s = [15,20,25,30,35]
        heat = pd.DataFrame(
            [[monthly_payment(loan_amount, r/100, t*12) for r in rates_s] for t in tenors_s],
            index=[f"{t}Y" for t in tenors_s],
            columns=[f"{r:.1f}%" for r in rates_s])
        fig_heat = go.Figure(go.Heatmap(
            z=heat.values, x=heat.columns, y=heat.index,
            colorscale=[[0,"#e8f8f2"],[0.5,"#f7dc6f"],[1,"#c0392b"]],
            text=[[f"S${v:,.0f}" for v in row] for row in heat.values],
            texttemplate="%{text}", textfont=dict(size=10), showscale=False))
        fig_heat.update_layout(height=260,paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                                font=dict(family="DM Sans",color="#0f1923"),
                                title="Monthly Payment: Rate × Tenor",
                                margin=dict(l=0,r=0,t=40,b=0),
                                xaxis_title="Interest Rate",yaxis_title="Tenor")
        st.plotly_chart(fig_heat, use_container_width=True)

    with ss2:
        pvs   = np.arange(1_000_000, 5_500_000, 250_000)
        tdsrs = [(monthly_payment(pv*(1-down_pct/100), ir_yr1/100, months_total)+existing_debt)
                  /total_rec_yr1*100 for pv in pvs]
        fig_tdsr = go.Figure()
        fig_tdsr.add_trace(go.Scatter(x=pvs, y=tdsrs, mode="lines",
                                       line=dict(color="#1e7e5c",width=2.5),
                                       fill="tozeroy",fillcolor="rgba(30,126,92,0.1)"))
        fig_tdsr.add_hline(y=55,line=dict(color="#c0392b",dash="dash",width=1.5),
                            annotation_text="MAS 55%",annotation_position="top right")
        fig_tdsr.add_vline(x=property_value,line=dict(color="#2980b9",dash="dot",width=1.5),
                            annotation_text="Current")
        fig_tdsr.update_layout(height=260,paper_bgcolor="#f7f4ef",plot_bgcolor="#f7f4ef",
                                font=dict(family="DM Sans",color="#0f1923"),
                                title="TDSR vs Property Value (Yr-1 Joint Income)",
                                margin=dict(l=0,r=0,t=40,b=0),showlegend=False,
                                xaxis=dict(tickformat=",.0f",gridcolor="#e0dbd2"),
                                yaxis=dict(tickformat=".0f",ticksuffix="%",gridcolor="#e0dbd2"))
        st.plotly_chart(fig_tdsr, use_container_width=True)

    # Down payment % sensitivity
    st.markdown('<div class="section-label">Down Payment vs Surplus / TDSR</div>', unsafe_allow_html=True)
    dp_pcts = list(range(10, 76, 5))
    dp_surp = []
    dp_tdsr = []
    for dp_p in dp_pcts:
        la = property_value * (1 - dp_p/100)
        pm = monthly_payment(la, ir_yr1/100, months_total)
        cm = max(pm - cpf_monthly, 0)
        dp_surp.append(net_home_yr1 - cm - total_exp - existing_debt)
        dp_tdsr.append((pm+existing_debt)/total_rec_yr1*100 if total_rec_yr1>0 else 999)

    fig_dp = make_subplots(specs=[[{"secondary_y":True}]])
    fig_dp.add_trace(go.Bar(x=dp_pcts, y=dp_surp,
                             marker_color=["#1e7e5c" if s>=0 else "#c0392b" for s in dp_surp],
                             name="Monthly Surplus", opacity=0.85), secondary_y=False)
    fig_dp.add_trace(go.Scatter(x=dp_pcts, y=dp_tdsr, name="TDSR (%)",
                                 mode="lines+markers", line=dict(color="#e67e22",width=2),
                                 marker=dict(size=5)), secondary_y=True)
    fig_dp.add_hline(y=55, line=dict(color="#c0392b",dash="dash",width=1.2),
                     secondary_y=True, annotation_text="55% TDSR Limit")
    fig_dp.add_vline(x=down_pct, line=dict(color="#2980b9",dash="dot",width=1.5),
                     annotation_text="Current")
    fig_dp.update_layout(height=280, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
                          font=dict(family="DM Sans",color="#0f1923"),
                          legend=dict(orientation="h",y=-0.3), margin=dict(l=0,r=0,t=10,b=10),
                          xaxis=dict(title="Down Payment %",gridcolor="#e0dbd2",dtick=5))
    fig_dp.update_yaxes(title_text="Monthly Surplus (SGD)", secondary_y=False, tickformat=",.0f", gridcolor="#e0dbd2")
    fig_dp.update_yaxes(title_text="TDSR (%)", secondary_y=True, tickformat=".0f", ticksuffix="%", showgrid=False)
    st.plotly_chart(fig_dp, use_container_width=True)

    # Full summary
    st.markdown('<div class="section-label">Full Summary</div>', unsafe_allow_html=True)
    sm1,sm2,sm3 = st.columns(3)
    with sm1:
        st.markdown("**Property & Loan**")
        for k,v in [("Property Value",fmt(property_value)),(f"Down Payment ({down_pct}%)",fmt(down_payment)),
                     ("Loan Amount",fmt(loan_amount)),("Tenor",f"{loan_tenor} yrs"),
                     ("Rates"," → ".join(f"{r:.2f}%" for r in rate_periods)),
                     ("Yr-1 Monthly Payment",fmt(pmt_yr1)),
                     (f"Cash {fmt(cash_mortgage)} · CPF {fmt(cpf_monthly)}","")]:
            st.write(f"{k}: **{v}**" if v else k)
    with sm2:
        st.markdown("**Year-1 Joint Income**")
        g_b1 = periods_b1[0]["fixed"]/12*(1+periods_b1[0]["var_pct"]/100)
        g_b2 = periods_b2[0]["fixed"]/12*(1+periods_b2[0]["var_pct"]/100)
        for k,v in [("B1 Gross Monthly",fmt(g_b1)),(f"B1 Tax (monthly)",fmt(tx_b1_yr1["Tax Payable"]/12)),
                     ("B1 Net Take-Home",fmt(net_b1_yr1)),
                     *([("B2 Net Take-Home",fmt(net_b2_yr1))] if include_b2 else []),
                     ("Joint Recognised (TDSR)",fmt(total_rec_yr1)),
                     (f"TDSR Yr-1",f"{tdsr_yr1:.1f}% (limit 55%)"),
                     ("Surplus Yr-1",f"{fmt(surplus_yr1)}/mo")]:
            st.write(f"{k}: **{v}**")
    with sm3:
        st.markdown("**Cost of Borrowing**")
        for k,v in [("Total Interest",fmt(total_interest)),(f"Interest-to-Loan",f"{total_interest/loan_amount*100:.1f}%"),
                     ("Total Property Cost",fmt(total_cost)),("Monthly Expenses",fmt(total_exp)),
                     (f"Months TDSR > 55%",str(months_over55)),
                     ("Overall Cash Surplus",fmt(cash_surplus))]:
            st.write(f"{k}: **{v}**")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 — EXIT STRATEGY
# ══════════════════════════════════════════════════════════════════════════════
with tab_exit:
    st.markdown('<div class="section-label">Exit Strategy — True Cost of Ownership</div>', unsafe_allow_html=True)
    st.caption("All costs incurred over a holding period, lease decay for leasehold properties, "
               "and net P&L at exit under different appreciation assumptions.")

    # ── Inputs row ─────────────────────────────────────────────────────────────
    xi1, xi2, xi3 = st.columns(3)
    with xi1:
        x_app = st.slider("Annual Appreciation (%)", 0.0, 8.0, 3.0, 0.5, key="exit_app") / 100
    with xi2:
        x_sell_pct = st.slider("Selling Costs — agent + legal (%)", 0.5, 3.0, 2.0, 0.25, key="exit_sell_pct") / 100
    with xi3:
        x_maint = monthly_maintenance  # from sidebar; shown as info
        st.metric("Monthly Maintenance Fee", fmt(x_maint))

    hold_years = sorted(set([1, 3, 5, 7, 10, 15, min(20, loan_tenor), loan_tenor]))
    hold_years = [y for y in hold_years if y <= loan_tenor]

    # ── One-time buying costs (fixed regardless of hold period) ────────────────
    buying_costs  = bsd + absd_net + legal_purchase + valuation_fee
    reno_cost     = renovation

    # ── Leasehold decay setup ──────────────────────────────────────────────────
    is_lh = is_leasehold
    if is_lh:
        lvf_buy = lease_value_factor(lease_remaining_yrs)
        fh_equiv = property_value / lvf_buy if lvf_buy > 0 else property_value

    def exit_value(hold_yrs):
        """Property value at exit, adjusted for appreciation and lease decay."""
        if is_lh:
            remaining_at_exit = max(0, lease_remaining_yrs - hold_yrs)
            lvf_exit = lease_value_factor(remaining_at_exit)
            return fh_equiv * (1 + x_app) ** hold_yrs * lvf_exit
        else:
            return property_value * (1 + x_app) ** hold_yrs

    # ── Cost-of-ownership table ────────────────────────────────────────────────
    st.markdown('<div class="section-label">Cumulative Cost Breakdown</div>', unsafe_allow_html=True)

    _cpf_rate_mo = 0.025 / 12
    _cpf_lump    = cpf_oa_b1 + cpf_oa_b2
    _cpf_mo_use  = cpf_b1 * cpf_b1_pct / 100 + cpf_b2 * cpf_b2_pct / 100

    def _cpf_refund_exit(months):
        ci_lump = _cpf_lump * ((1 + _cpf_rate_mo) ** months - 1)
        ci_mo   = sum(_cpf_mo_use * ((1 + _cpf_rate_mo) ** (months - j) - 1) for j in range(1, months + 1))
        return _cpf_lump + _cpf_mo_use * months + ci_lump + ci_mo

    cost_rows = []
    pnl_rows  = []
    for hy in hold_years:
        months       = hy * 12
        m_idx        = min(months - 1, len(df_amort) - 1)
        cum_interest = df_amort["Interest"].iloc[:m_idx + 1].sum()
        cum_maint    = x_maint * months
        ssd_exit     = calc_ssd(exit_value(hy), hy)
        selling_cost = exit_value(hy) * x_sell_pct + ssd_exit
        total_cost_hold = buying_costs + reno_cost + cum_maint + cum_interest

        cost_rows.append({
            "Hold Period":     f"{hy}yr",
            "Buying Costs":    buying_costs,
            "Renovation":      reno_cost,
            "Maintenance":     cum_maint,
            "Interest Paid":   cum_interest,
            "Selling Costs":   selling_cost,
            "Total Outflow":   total_cost_hold + selling_cost,
        })

        # P&L
        prop_val_exit = exit_value(hy)
        loan_bal_exit = df_amort["Balance"].iloc[m_idx]
        cpf_ref_exit  = _cpf_refund_exit(months)
        gross_sale    = prop_val_exit * (1 - x_sell_pct) - ssd_exit
        cash_in_hand  = gross_sale - loan_bal_exit - cpf_ref_exit
        cum_cash_paid = sum(
            max(df_amort[df_amort["Month"] == m]["Payment"].values[0]
                - _cpf_mo_use, 0)
            for m in range(1, months + 1)
            if m <= len(df_amort)
        )
        total_cash_inv = down_payment + buying_costs + reno_cost + cum_maint + cum_cash_paid
        net_gain       = cash_in_hand - (down_payment + buying_costs + reno_cost)
        ann_ret        = (1 + net_gain / total_cash_inv) ** (1 / hy) - 1 if total_cash_inv > 0 and hy > 0 else 0

        # Lease decay info
        if is_lh:
            rem_at_exit = max(0, lease_remaining_yrs - hy)
            pure_app    = property_value * (1 + x_app) ** hy
            decay_adj   = prop_val_exit - pure_app
        else:
            rem_at_exit = None
            decay_adj   = 0.0

        pnl_rows.append({
            "Hold Period":      f"{hy}yr",
            "Property Value":   prop_val_exit,
            "Lease Decay Adj":  decay_adj,
            "Gross Sale":       gross_sale,
            "Loan Balance":     loan_bal_exit,
            "CPF Refund":       cpf_ref_exit,
            "Cash in Hand":     cash_in_hand,
            "Cash Invested":    total_cash_inv,
            "Net Gain":         net_gain,
            "Ann. Return":      ann_ret,
            "_rem":             rem_at_exit,
        })

    # Display cost table
    df_cost = pd.DataFrame(cost_rows)
    df_cost_disp = df_cost.copy()
    for c in ["Buying Costs","Renovation","Maintenance","Interest Paid","Selling Costs","Total Outflow"]:
        df_cost_disp[c] = df_cost_disp[c].map(lambda x: f"S${x:,.0f}")
    st.dataframe(df_cost_disp, use_container_width=True, hide_index=True)

    # ── Cost composition chart ─────────────────────────────────────────────────
    xc1, xc2 = st.columns(2)
    with xc1:
        fig_cost = go.Figure()
        cost_layers = [
            ("Buying Costs",  [r["Buying Costs"]  for r in cost_rows], "#2980b9"),
            ("Renovation",    [r["Renovation"]    for r in cost_rows], "#8e44ad"),
            ("Maintenance",   [r["Maintenance"]   for r in cost_rows], "#e67e22"),
            ("Interest Paid", [r["Interest Paid"] for r in cost_rows], "#c0392b"),
            ("Selling Costs", [r["Selling Costs"] for r in cost_rows], "#7f8c8d"),
        ]
        xlbls = [r["Hold Period"] for r in cost_rows]
        for name, vals, color in cost_layers:
            fig_cost.add_trace(go.Bar(name=name, x=xlbls, y=vals, marker_color=color))
        fig_cost.update_layout(
            barmode="stack", height=320, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
            font=dict(family="DM Sans", color="#0f1923"),
            title=dict(text="Cumulative Cost of Ownership", font=dict(size=12)),
            legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
            margin=dict(l=0, r=0, t=40, b=10),
            xaxis=dict(title="Hold Period", gridcolor="#e0dbd2"),
            yaxis=dict(tickformat=",.0f", gridcolor="#e0dbd2", title="SGD"),
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    with xc2:
        # Property value vs total outflow
        prop_vals = [exit_value(hy) for hy in hold_years]
        outflows  = [r["Total Outflow"] for r in cost_rows]
        fig_pv = go.Figure()
        fig_pv.add_trace(go.Scatter(x=xlbls, y=prop_vals, name="Property Value at Exit",
                                     mode="lines+markers", line=dict(color="#1e7e5c", width=2.5),
                                     marker=dict(size=7)))
        fig_pv.add_trace(go.Scatter(x=xlbls, y=outflows, name="Total Outflow (all costs)",
                                     mode="lines+markers", line=dict(color="#c0392b", width=2, dash="dash"),
                                     marker=dict(size=7)))
        if is_lh:
            no_decay = [property_value * (1 + x_app) ** hy for hy in hold_years]
            fig_pv.add_trace(go.Scatter(x=xlbls, y=no_decay, name="Value w/o Lease Decay",
                                         mode="lines", line=dict(color="#aaa", width=1.5, dash="dot")))
        fig_pv.update_layout(
            height=320, paper_bgcolor="#f7f4ef", plot_bgcolor="#f7f4ef",
            font=dict(family="DM Sans", color="#0f1923"),
            title=dict(text="Property Value vs Total Outflow at Exit", font=dict(size=12)),
            legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
            margin=dict(l=0, r=0, t=40, b=10),
            xaxis=dict(title="Hold Period", gridcolor="#e0dbd2"),
            yaxis=dict(tickformat=",.0f", gridcolor="#e0dbd2", title="SGD"),
        )
        st.plotly_chart(fig_pv, use_container_width=True)

    # ── P&L table ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Net P&L at Exit</div>', unsafe_allow_html=True)
    df_pnl = pd.DataFrame(pnl_rows)
    pnl_disp = df_pnl[["Hold Period","Property Value","Lease Decay Adj","Gross Sale",
                         "Loan Balance","CPF Refund","Cash in Hand","Cash Invested","Net Gain","Ann. Return"]].copy()
    if not is_lh:
        pnl_disp = pnl_disp.drop(columns=["Lease Decay Adj"])
    for c in ["Property Value","Lease Decay Adj","Gross Sale","Loan Balance",
               "CPF Refund","Cash in Hand","Cash Invested","Net Gain"]:
        if c in pnl_disp.columns:
            pnl_disp[c] = pnl_disp[c].map(lambda x: f"S${x:,.0f}")
    pnl_disp["Ann. Return"] = df_pnl["Ann. Return"].map(lambda x: f"{x:.1%}")
    pnl_disp["Cash in Hand"] = [
        f"{'🟢' if r['Cash in Hand']>=0 else '🔴'} S${r['Cash in Hand']:,.0f}"
        for r in pnl_rows
    ]
    st.dataframe(pnl_disp, use_container_width=True, hide_index=True)

    if is_lh:
        st.caption(f"**Lease Decay Adj** = additional value loss due to shorter remaining lease (Bala's curve). "
                   f"At purchase: {lease_remaining_yrs}yr remaining (factor {lease_value_factor(lease_remaining_yrs):.2f}). "
                   f"Freehold-equivalent reference: {fmt(fh_equiv)}.")

    # ── Breakeven appreciation needed ──────────────────────────────────────────
    st.markdown('<div class="section-label">Break-Even Appreciation Needed</div>', unsafe_allow_html=True)
    be2_rows = []
    for hy in hold_years:
        months    = hy * 12
        m_idx     = min(months - 1, len(df_amort) - 1)
        cum_int   = df_amort["Interest"].iloc[:m_idx + 1].sum()
        cum_maint = x_maint * months
        total_out = buying_costs + reno_cost + cum_int + cum_maint
        sell_c_pct = x_sell_pct
        ssd_yrs    = hy
        # Solve for r: property_value*(1+r)^hy*(1-sell_pct) - ssd(...) - loan_bal - cpf_ref = down_pmt + buying + reno + maint
        # Approximation: ignore SSD iteration, use linear solve
        loan_bal   = df_amort["Balance"].iloc[m_idx]
        cpf_ref    = _cpf_refund_exit(months)
        target_net = down_payment + buying_costs + reno_cost + cum_maint + loan_bal + cpf_ref
        # property_value*(1+r)^hy * (1-sell_pct) = target_net → (1+r)^hy = target_net / (pv*(1-sell_pct))
        if is_lh:
            # Need: fh_equiv*(1+r)^hy * lvf_exit * (1-sell_pct) = target_net
            rem_at_exit = max(0, lease_remaining_yrs - hy)
            lvf_exit    = lease_value_factor(rem_at_exit)
            denom       = fh_equiv * lvf_exit * (1 - sell_c_pct)
        else:
            denom = property_value * (1 - sell_c_pct)
        if denom > 0:
            r_be = (target_net / denom) ** (1 / hy) - 1 if hy > 0 else 0
        else:
            r_be = float("nan")
        be2_rows.append({
            "Hold Period":        f"{hy}yr",
            "Total Outflow":      fmt(total_out),
            "Loan Bal + CPF":     fmt(loan_bal + cpf_ref),
            "Target Sale Price":  fmt(target_net / (1 - sell_c_pct)),
            "Break-Even App. p.a.": f"{r_be:.1%}" if not math.isnan(r_be) else "—",
            "vs Selected App.":   f"{'✅' if (not math.isnan(r_be) and r_be <= x_app) else '❌'} {r_be:.1%}" if not math.isnan(r_be) else "—",
        })
    st.dataframe(pd.DataFrame(be2_rows), use_container_width=True, hide_index=True)
    st.caption("Break-even = minimum annual appreciation needed so that sale proceeds cover all capital invested, "
               "loan balance, CPF refund, and selling costs.")
