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
from plotly.subplots import make_subplots

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
    if not code or not isinstance(code, str):
        return str(code)
    parts = code.strip().upper().split("-")
    if len(parts) == 2:
        return f"{MONTH_MAP.get(parts[0], parts[0])} – {MONTH_MAP.get(parts[1], parts[1])}"
    return code


@st.cache_data(show_spinner="Φόρτωση δεδομένων...")
def load_data(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name="data",
        header=1,
    )
    # Καθαρισμός τύπων
    for col in ["Τζίρος", "Συν.ποσ.πωλήσεων", "ΠΛΤ"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Έτος"] = pd.to_numeric(df["Έτος"], errors="coerce")
    df["Έτος"] = df["Έτος"].astype("Int64")

    # String columns — γεμίζουμε NaN με "" για να δουλεύουν τα filters
    for col in ["Οικογένεια", "Ομάδα", "Κατηγορία", "Υποκατηγορία",
                "Ομάδα Υποκ/των", "Like to Like", "Διάστημα"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    df["Μέση Τιμή"] = np.where(
        df["Συν.ποσ.πωλήσεων"] > 0,
        df["Τζίρος"] / df["Συν.ποσ.πωλήσεων"],
        np.nan,
    )
    df.dropna(subset=["Τζίρος", "Έτος"], inplace=True)
    return df


def fmt_eur(val: float) -> str:
    return f"€{val:,.0f}"


def fmt_qty(val: float) -> str:
    return f"{int(val):,}"


def pct_delta(new: float, old) -> str | None:
    try:
        if old and float(old) != 0:
            return f"{(float(new) - float(old)) / abs(float(old)) * 100:+.1f}%"
    except Exception:
        pass
    return None


def sorted_nonempty(series: pd.Series) -> list:
    return sorted([x for x in series.dropna().unique() if str(x).strip() != ""])


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Sell-Out Dashboard", page_icon="📊", layout="wide")
st.title("📊 Sell-Out Dashboard")

# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD
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

df_all = load_data(uploaded.read())

raw_periods  = [p for p in df_all["Διάστημα"].unique() if p]
period_code  = raw_periods[0] if raw_periods else "—"
period_label = period_to_label(period_code)

st.caption(
    f"📅 Περίοδος: **{period_label}** (`{period_code}`)  |  "
    f"Αρχείο: `{uploaded.name}`  |  Εγγραφές: {len(df_all):,}"
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Tree Filters  (Οικογένεια → Ομάδα → Κατηγορία → Υποκατηγορία)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("🌳 Φίλτρα")

    # ── Οικογένεια ──────────────────────────────────────────────────────────
    all_families = sorted_nonempty(df_all["Οικογένεια"])
    sel_family   = st.multiselect("Οικογένεια", all_families, default=all_families, key="fam")

    # ── Ομάδα  (εξαρτάται από Οικογένεια) ───────────────────────────────────
    df_f = df_all[df_all["Οικογένεια"].isin(sel_family)] if sel_family else df_all
    all_groups = sorted_nonempty(df_f["Ομάδα"])
    sel_group  = st.multiselect("Ομάδα", all_groups, default=all_groups, key="grp")

    # ── Κατηγορία  (εξαρτάται από Ομάδα) ────────────────────────────────────
    df_g = df_f[df_f["Ομάδα"].isin(sel_group)] if sel_group else df_f
    all_cats = sorted_nonempty(df_g["Κατηγορία"])
    sel_cat  = st.multiselect("Κατηγορία", all_cats, default=all_cats, key="cat")

    # ── Υποκατηγορία  (εξαρτάται από Κατηγορία) ────────────────────────────
    df_c = df_g[df_g["Κατηγορία"].isin(sel_cat)] if sel_cat else df_g
    all_subcats = sorted_nonempty(df_c["Υποκατηγορία"])
    sel_subcat  = st.multiselect("Υποκατηγορία", all_subcats, default=all_subcats, key="sub")

    st.divider()
    # ── Reset button ─────────────────────────────────────────────────────────
    if st.button("🔄 Καθαρισμός φίλτρων"):
        for k in ["fam", "grp", "cat", "sub"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_family: df = df[df["Οικογένεια"].isin(sel_family)]
if sel_group:  df = df[df["Ομάδα"].isin(sel_group)]
if sel_cat:    df = df[df["Κατηγορία"].isin(sel_cat)]
if sel_subcat: df = df[df["Υποκατηγορία"].isin(sel_subcat)]

if df.empty:
    st.warning("⚠️ Δεν υπάρχουν δεδομένα με τα επιλεγμένα φίλτρα.")
    st.stop()

years     = sorted(df["Έτος"].dropna().unique().tolist())
years_str = [str(int(y)) for y in years]

# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────────────────
st.subheader(f"📌 KPIs — {period_label}")

ll_df   = df[df["Like to Like"] == "L/L"]
kpi_ll_tz  = ll_df.groupby("Έτος")["Τζίρος"].sum()
kpi_ll_qty = ll_df.groupby("Έτος")["Συν.ποσ.πωλήσεων"].sum()
kpi_tot_tz  = df.groupby("Έτος")["Τζίρος"].sum()
kpi_tot_qty = df.groupby("Έτος")["Συν.ποσ.πωλήσεων"].sum()
kpi_avg = df.groupby("Έτος").apply(
    lambda x: x["Τζίρος"].sum() / x["Συν.ποσ.πωλήσεων"].sum()
    if x["Συν.ποσ.πωλήσεων"].sum() > 0 else np.nan,
    include_groups=False,
)

last = years[-1]  if years            else None
prev = years[-2]  if len(years) >= 2  else None

# --- Row 1: Τζίρος ---
st.markdown("**Τζίρος (€)**")
c1, c2, c3 = st.columns(3)
if last:
    v = float(kpi_ll_tz.get(last, 0))
    c1.metric("L/L", fmt_eur(v),
              delta=pct_delta(v, kpi_ll_tz.get(prev, None)),
              help="Τζίρος L/L καταστημάτων")
    v = float(kpi_tot_tz.get(last, 0))
    c2.metric("Σύνολο Δικτύου", fmt_eur(v),
              delta=pct_delta(v, kpi_tot_tz.get(prev, None)))
    v = float(kpi_avg.get(last, np.nan))
    c3.metric("Μέση Τιμή", f"€{v:.2f}" if not np.isnan(v) else "—",
              delta=pct_delta(v, kpi_avg.get(prev, None)))

# --- Row 2: Τεμάχια ---
st.markdown("**Τεμάχια**")
d1, d2 = st.columns(3)[:2]
if last:
    v = float(kpi_ll_qty.get(last, 0))
    d1.metric("L/L", fmt_qty(v),
              delta=pct_delta(v, kpi_ll_qty.get(prev, None)),
              help="Τεμάχια L/L καταστημάτων")
    v = float(kpi_tot_qty.get(last, 0))
    d2.metric("Σύνολο Δικτύου", fmt_qty(v),
              delta=pct_delta(v, kpi_tot_qty.get(prev, None)))

if prev:
    st.caption(f"Δέλτα % vs {int(prev)}")

# ─────────────────────────────────────────────────────────────────────────────
# ΕΞΕΛΙΞΗ ΑΝΑ ΧΡΟΝΙΑ — Τζίρος & Τεμάχια
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Εξέλιξη ανά Έτος")

tab_tz, tab_qty, tab_avg = st.tabs(["Τζίρος", "Τεμάχια", "Μέση Τιμή"])

with tab_tz:
    fig = go.Figure()
    fig.add_trace(go.Bar(name="L/L", x=years_str,
                         y=[float(kpi_ll_tz.get(y, 0)) for y in years],
                         marker_color=COLORS[0]))
    fig.add_trace(go.Bar(name="Σύνολο", x=years_str,
                         y=[float(kpi_tot_tz.get(y, 0)) for y in years],
                         marker_color=COLORS[1]))
    fig.update_layout(barmode="group", template="plotly_white",
                      xaxis_title="Έτος", yaxis_title="Τζίρος (€)",
                      legend=dict(orientation="h", y=1.12), height=380)
    st.plotly_chart(fig, use_container_width=True)

with tab_qty:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="L/L", x=years_str,
                          y=[float(kpi_ll_qty.get(y, 0)) for y in years],
                          marker_color=COLORS[2]))
    fig2.add_trace(go.Bar(name="Σύνολο", x=years_str,
                          y=[float(kpi_tot_qty.get(y, 0)) for y in years],
                          marker_color=COLORS[3]))
    fig2.update_layout(barmode="group", template="plotly_white",
                       xaxis_title="Έτος", yaxis_title="Τεμάχια",
                       legend=dict(orientation="h", y=1.12), height=380)
    st.plotly_chart(fig2, use_container_width=True)

with tab_avg:
    fig3 = px.line(x=years_str,
                   y=[float(kpi_avg.get(y, np.nan)) for y in years],
                   markers=True,
                   labels={"x": "Έτος", "y": "Μέση Τιμή (€)"},
                   template="plotly_white",
                   color_discrete_sequence=[COLORS[4]])
    fig3.update_layout(height=340)
    st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΑΝΑΛΥΣΗ ΑΝΑ ΚΑΝΑΛΙ
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🏪 Ανάλυση ανά Κανάλι Διανομής")

ch_agg = (
    df.groupby(["Έτος", "Ομάδα Υποκ/των"])
      .agg(Τζίρος=("Τζίρος", "sum"), Τεμάχια=("Συν.ποσ.πωλήσεων", "sum"))
      .reset_index()
)
ch_agg["Έτος"] = ch_agg["Έτος"].astype(str)

ch_tab1, ch_tab2 = st.tabs(["Τζίρος ανά Κανάλι", "Τεμάχια ανά Κανάλι"])

for tab, metric, label in [
    (ch_tab1, "Τζίρος", "Τζίρος (€)"),
    (ch_tab2, "Τεμάχια", "Τεμάχια"),
]:
    with tab:
        fig = px.bar(ch_agg, x="Ομάδα Υποκ/των", y=metric, color="Έτος",
                     barmode="group",
                     labels={metric: label, "Ομάδα Υποκ/των": "Κανάλι"},
                     template="plotly_white", height=430,
                     color_discrete_sequence=COLORS)
        fig.update_xaxes(tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Πίνακας"):
            pivot = (
                ch_agg.pivot(index="Ομάδα Υποκ/των", columns="Έτος", values=metric)
                      .fillna(0).astype(int)
            )
            st.dataframe(pivot.style.format("{:,}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΤΖΙΡΟΣ & ΤΕΜΑΧΙΑ vs ΚΑΤΗΓΟΡΙΕΣ  (tree tabs)
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🗂️ Ανάλυση ανά Κατηγορία")

# Επίπεδα δέντρου
LEVELS = ["Οικογένεια", "Ομάδα", "Κατηγορία", "Υποκατηγορία"]
level_tabs = st.tabs(LEVELS)

for lev, ltab in zip(LEVELS, level_tabs):
    with ltab:
        agg = (
            df.groupby(["Έτος", lev])
              .agg(Τζίρος=("Τζίρος", "sum"), Τεμάχια=("Συν.ποσ.πωλήσεων", "sum"))
              .reset_index()
        )
        # φιλτράρισμα κενών
        agg = agg[agg[lev].str.strip() != ""]
        agg["Έτος"] = agg["Έτος"].astype(str)

        if agg.empty:
            st.info("Δεν υπάρχουν δεδομένα για αυτό το επίπεδο.")
            continue

        inner1, inner2 = st.tabs(["Τζίρος", "Τεμάχια"])

        for inner_tab, metric, ylabel in [
            (inner1, "Τζίρος", "Τζίρος (€)"),
            (inner2, "Τεμάχια", "Τεμάχια"),
        ]:
            with inner_tab:
                fig = px.bar(
                    agg, x=lev, y=metric, color="Έτος",
                    barmode="group",
                    labels={metric: ylabel},
                    template="plotly_white", height=470,
                    color_discrete_sequence=COLORS,
                )
                fig.update_xaxes(tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("📋 Πίνακας"):
                    pivot = (
                        agg.pivot(index=lev, columns="Έτος", values=metric)
                           .fillna(0).astype(int)
                    )
                    st.dataframe(pivot.style.format("{:,}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Sell-Out Dashboard · Φίλτρα: Οικογένεια → Ομάδα → Κατηγορία → Υποκατηγορία · "
    "Η περίοδος ανιχνεύεται από τη στήλη Διάστημα"
)
