"""
Sell-Out Dashboard — Streamlit App
===================================
Deploy: GitHub → Streamlit Cloud
Τρέξε τοπικά: streamlit run sell_out_dashboard.py
"""

import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# ΣΤΑΘΕΡΕΣ
# ─────────────────────────────────────────────────────────────────────────────
MONTH_MAP = {
    "ΙΑΝ":  "Ιανουάριος",  "ΦΕΒ":  "Φεβρουάριος", "ΜΑΡ":  "Μάρτιος",
    "ΑΠΡ":  "Απρίλιος",    "ΜΑΙ":  "Μάιος",        "ΜΑΪ":  "Μάιος",
    "ΙΟΥΝ": "Ιούνιος",     "ΙΟΥΛ": "Ιούλιος",      "ΑΥΓ":  "Αύγουστος",
    "ΣΕΠ":  "Σεπτέμβριος", "ΟΚΤ":  "Οκτώβριος",    "ΝΟΕ":  "Νοέμβριος",
    "ΔΕΚ":  "Δεκέμβριος",
}

COLORS = px.colors.qualitative.Set2


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def period_to_label(code: str) -> str:
    """ΙΑΝ-ΜΑΡ  →  Ιανουάριος – Μάρτιος"""
    if not code or not isinstance(code, str):
        return str(code)
    parts = code.strip().upper().split("-")
    if len(parts) == 2:
        start = MONTH_MAP.get(parts[0], parts[0])
        end   = MONTH_MAP.get(parts[1], parts[1])
        return f"{start} – {end}"
    return code


@st.cache_data(show_spinner="Φόρτωση δεδομένων...")
def load_data(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name="data",
        header=1,
        dtype_backend="numpy_nullable",
    )
    df["Τζίρος"]            = pd.to_numeric(df["Τζίρος"],            errors="coerce")
    df["Συν.ποσ.πωλήσεων"] = pd.to_numeric(df["Συν.ποσ.πωλήσεων"], errors="coerce")
    df["ΠΛΤ"]               = pd.to_numeric(df["ΠΛΤ"],               errors="coerce")
    df["Έτος"]              = pd.to_numeric(df["Έτος"],              errors="coerce").astype("Int64")
    df["Μέση Τιμή"]         = np.where(
        df["Συν.ποσ.πωλήσεων"] > 0,
        df["Τζίρος"] / df["Συν.ποσ.πωλήσεων"],
        np.nan,
    )
    df.dropna(subset=["Τζίρος", "Έτος"], inplace=True)
    return df


def fmt_eur(val: float) -> str:
    return f"€{val:,.0f}"


def pct_delta(new: float, old) -> str | None:
    if old is not None and old != 0:
        return f"{(new - old) / abs(old) * 100:+.1f}%"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sell-Out Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Sell-Out Dashboard")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Upload
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις")
    uploaded = st.file_uploader(
        "Ανέβασε το αρχείο Excel",
        type=["xlsx", "xls"],
        help="Το αρχείο πρέπει να έχει sheet με όνομα 'data'",
    )

if uploaded is None:
    st.info("👈 Ανέβασε αρχείο Excel από το sidebar για να ξεκινήσει η ανάλυση.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
df_all = load_data(uploaded.read())

# Ανίχνευση περιόδου από τη στήλη Διάστημα (π.χ. ΙΑΝ-ΜΑΡ)
raw_periods  = df_all["Διάστημα"].dropna().unique().tolist()
period_code  = raw_periods[0] if raw_periods else "—"
period_label = period_to_label(period_code)

st.caption(
    f"📅 Περίοδος: **{period_label}** (`{period_code}`)  |  "
    f"Αρχείο: `{uploaded.name}`  |  Εγγραφές: {len(df_all):,}"
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Cascading Filters
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("🔍 Φίλτρα")

    families   = sorted(df_all["Οικογένεια"].dropna().unique().tolist())
    sel_family = st.multiselect("Οικογένεια", families, default=families)

    mask_fam  = df_all["Οικογένεια"].isin(sel_family) if sel_family else pd.Series(True, index=df_all.index)
    groups    = sorted(df_all.loc[mask_fam, "Ομάδα"].dropna().unique().tolist())
    sel_group = st.multiselect("Ομάδα", groups, default=groups)

    mask_grp = df_all["Ομάδα"].isin(sel_group) if sel_group else mask_fam
    cats     = sorted(df_all.loc[mask_grp, "Κατηγορία"].dropna().unique().tolist())
    sel_cat  = st.multiselect("Κατηγορία", cats, default=cats)

# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_family: df = df[df["Οικογένεια"].isin(sel_family)]
if sel_group:  df = df[df["Ομάδα"].isin(sel_group)]
if sel_cat:    df = df[df["Κατηγορία"].isin(sel_cat)]

if df.empty:
    st.warning("⚠️ Δεν υπάρχουν δεδομένα με τα επιλεγμένα φίλτρα.")
    st.stop()

years     = sorted(df["Έτος"].dropna().unique().tolist())
years_str = [str(y) for y in years]

# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────────────────
st.subheader(f"📌 KPIs — {period_label}")

ll_df   = df[df["Like to Like"] == "L/L"]
kpi_ll  = ll_df.groupby("Έτος")["Τζίρος"].sum()
kpi_tot = df.groupby("Έτος")["Τζίρος"].sum()
kpi_avg = df.groupby("Έτος").apply(
    lambda x: x["Τζίρος"].sum() / x["Συν.ποσ.πωλήσεων"].sum()
    if x["Συν.ποσ.πωλήσεων"].sum() > 0 else np.nan,
    include_groups=False,
)

last = years[-1]  if years           else None
prev = years[-2]  if len(years) >= 2 else None

col1, col2, col3 = st.columns(3)
if last:
    v_ll  = float(kpi_ll.get(last,  0))
    v_tot = float(kpi_tot.get(last, 0))
    v_avg = float(kpi_avg.get(last, np.nan))

    col1.metric(
        "Τζίρος L/L", fmt_eur(v_ll),
        delta=pct_delta(v_ll,  float(kpi_ll.get(prev,  0)) if prev else None),
        help="Μόνο L/L καταστήματα",
    )
    col2.metric(
        "Τζίρος Συνόλου Δικτύου", fmt_eur(v_tot),
        delta=pct_delta(v_tot, float(kpi_tot.get(prev, 0)) if prev else None),
    )
    col3.metric(
        "Μέση Τιμή Πώλησης",
        f"€{v_avg:.2f}" if not np.isnan(v_avg) else "—",
        delta=pct_delta(v_avg, float(kpi_avg.get(prev, np.nan)) if prev else None),
    )
    if prev:
        st.caption(f"Δέλτα % vs {prev}")

# ─────────────────────────────────────────────────────────────────────────────
# ΕΞΕΛΙΞΗ ΤΖΙΡΟΥ
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Εξέλιξη Τζίρου ανά Έτος")

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name="Τζίρος L/L",
    x=years_str,
    y=[float(kpi_ll.get(y,  0)) for y in years],
    marker_color=COLORS[0],
))
fig_bar.add_trace(go.Bar(
    name="Τζίρος Συνόλου",
    x=years_str,
    y=[float(kpi_tot.get(y, 0)) for y in years],
    marker_color=COLORS[1],
))
fig_bar.update_layout(
    barmode="group", template="plotly_white",
    xaxis_title="Έτος", yaxis_title="Τζίρος (€)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=380,
)
st.plotly_chart(fig_bar, use_container_width=True)

fig_avg = px.line(
    x=years_str,
    y=[float(kpi_avg.get(y, np.nan)) for y in years],
    markers=True,
    labels={"x": "Έτος", "y": "Μέση Τιμή (€)"},
    title="Μέση Τιμή Πώλησης ανά Έτος",
    template="plotly_white",
    color_discrete_sequence=[COLORS[2]],
)
fig_avg.update_layout(height=300)
st.plotly_chart(fig_avg, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΑΝΑΛΥΣΗ ΑΝΑ ΚΑΝΑΛΙ
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🏪 Ανάλυση ανά Κανάλι Διανομής")

ch_df = (
    df.groupby(["Έτος", "Ομάδα Υποκ/των"])["Τζίρος"]
      .sum()
      .reset_index()
)
ch_df["Έτος"] = ch_df["Έτος"].astype(str)

fig_ch = px.bar(
    ch_df, x="Ομάδα Υποκ/των", y="Τζίρος", color="Έτος",
    barmode="group",
    labels={"Τζίρος": "Τζίρος (€)", "Ομάδα Υποκ/των": "Κανάλι"},
    template="plotly_white", height=430,
    color_discrete_sequence=COLORS,
)
fig_ch.update_xaxes(tickangle=-20)
st.plotly_chart(fig_ch, use_container_width=True)

with st.expander("📋 Πίνακας ανά Κανάλι"):
    pivot_ch = (
        ch_df.pivot(index="Ομάδα Υποκ/των", columns="Έτος", values="Τζίρος")
             .fillna(0).astype(int)
    )
    st.dataframe(pivot_ch.style.format("{:,}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΤΖΙΡΟΣ vs ΚΑΤΗΓΟΡΙΕΣ
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🗂️ Τζίρος vs Κατηγορίες")

tab1, tab2, tab3 = st.tabs(["Οικογένεια", "Ομάδα", "Κατηγορία"])


def category_tab(col: str, tab):
    data = (
        df.groupby(["Έτος", col])["Τζίρος"]
          .sum()
          .reset_index()
    )
    data["Έτος"] = data["Έτος"].astype(str)
    fig = px.bar(
        data, x=col, y="Τζίρος", color="Έτος",
        barmode="group",
        labels={"Τζίρος": "Τζίρος (€)"},
        template="plotly_white", height=460,
        color_discrete_sequence=COLORS,
    )
    fig.update_xaxes(tickangle=-35)
    tab.plotly_chart(fig, use_container_width=True)
    with tab.expander("📋 Πίνακας"):
        pivot = (
            data.pivot(index=col, columns="Έτος", values="Τζίρος")
                .fillna(0).astype(int)
        )
        tab.dataframe(pivot.style.format("{:,}"), use_container_width=True)


category_tab("Οικογένεια", tab1)
category_tab("Ομάδα",      tab2)
category_tab("Κατηγορία",  tab3)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Sell-Out Dashboard · Η περίοδος ανιχνεύεται αυτόματα από τα δεδομένα (στήλη Διάστημα)"
)
