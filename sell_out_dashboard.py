"""
Sell-Out Dashboard — Streamlit App
Tested: pandas==2.2.3, plotly==5.24.1, streamlit==1.57.0
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

STR_COLS = ["Οικογένεια", "Ομάδα", "Κατηγορία", "Υποκατηγορία",
            "Ομάδα Υποκ/των", "Like to Like", "Διάστημα"]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def period_to_label(code):
    if not code or not isinstance(code, str):
        return str(code)
    parts = code.strip().upper().split("-")
    if len(parts) == 2:
        return "{} \u2013 {}".format(
            MONTH_MAP.get(parts[0], parts[0]),
            MONTH_MAP.get(parts[1], parts[1]),
        )
    return code


@st.cache_data(show_spinner="Φόρτωση δεδομένων...")
def load_data(file_bytes):
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="data", header=1)

    # Αριθμητικές στήλες
    for col in ["Τζίρος", "Συν.ποσ.πωλήσεων", "ΠΛΤ"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Έτος ως int (απλό, χωρίς nullable)
    if "Έτος" in df.columns:
        df["Έτος"] = pd.to_numeric(df["Έτος"], errors="coerce")
        df = df.dropna(subset=["Έτος"])
        df["Έτος"] = df["Έτος"].astype(int)

    # String στήλες — καθαρά strings, χωρίς NaN
    for col in STR_COLS:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    df = df.dropna(subset=["Τζίρος"])
    df = df[df["Τζίρος"] != 0]
    df = df.reset_index(drop=True)
    return df


def calc_avg_price(sub_df):
    """Μέση τιμή ανά έτος: Τζίρος / Τεμάχια."""
    g = sub_df.groupby("Έτος", sort=True).agg(
        tz=("Τζίρος", "sum"),
        qty=("Συν.ποσ.πωλήσεων", "sum"),
    )
    g["avg"] = np.where(g["qty"] > 0, g["tz"] / g["qty"], np.nan)
    return g["avg"]


def fmt_eur(val):
    return "\u20ac{:,.0f}".format(float(val))


def fmt_qty(val):
    return "{:,}".format(int(float(val)))


def delta_str(new_val, old_val):
    """Επιστρέφει string '+X.X%' ή None."""
    try:
        n, o = float(new_val), float(old_val)
        if not np.isnan(n) and not np.isnan(o) and o != 0:
            return "{:+.1f}%".format((n - o) / abs(o) * 100)
    except Exception:
        pass
    return None


def nonempty_sorted(series):
    return sorted({str(x) for x in series if str(x).strip() != ""})


def bar_chart(data, x_col, y_col, y_label, title=None):
    fig = px.bar(
        data, x=x_col, y=y_col, color="Έτος",
        barmode="group",
        labels={y_col: y_label, x_col: x_col},
        template="plotly_white",
        height=450,
        color_discrete_sequence=COLORS,
        title=title,
    )
    fig.update_xaxes(tickangle=-30)
    fig.update_layout(legend=dict(orientation="h", y=1.10, x=0))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Sell-Out Dashboard", page_icon="\U0001f4ca", layout="wide")
st.title("\U0001f4ca Sell-Out Dashboard")

# ── Upload ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("\u2699\ufe0f \u03a1\u03c5\u03b8\u03bc\u03af\u03c3\u03b5\u03b9\u03c2")
    uploaded = st.file_uploader(
        "Ανέβασε το αρχείο Excel",
        type=["xlsx", "xls"],
        help="Sheet name: 'data', header στη 2η γραμμή",
    )

if uploaded is None:
    st.info("\U0001f448 Ανέβασε αρχείο Excel από το sidebar.")
    st.stop()

df_all = load_data(uploaded.read())

# Περίοδος από δεδομένα
periods     = [p for p in df_all["Διάστημα"].unique() if p.strip()]
period_code = periods[0] if periods else "—"
period_lbl  = period_to_label(period_code)

st.caption(
    "📅 Περίοδος: **{lbl}** (`{code}`)  |  Αρχείο: `{fn}`  |  Εγγραφές: {n:,}".format(
        lbl=period_lbl, code=period_code, fn=uploaded.name, n=len(df_all)
    )
)

# ── Sidebar filters (tree) ────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("\U0001f333 Φίλτρα")

    all_fam = nonempty_sorted(df_all["Οικογένεια"])
    sel_fam = st.multiselect("Οικογένεια", all_fam, default=all_fam, key="fam")

    df_f    = df_all[df_all["Οικογένεια"].isin(sel_fam)] if sel_fam else df_all
    all_grp = nonempty_sorted(df_f["Ομάδα"])
    sel_grp = st.multiselect("Ομάδα", all_grp, default=all_grp, key="grp")

    df_g    = df_f[df_f["Ομάδα"].isin(sel_grp)] if sel_grp else df_f
    all_cat = nonempty_sorted(df_g["Κατηγορία"])
    sel_cat = st.multiselect("Κατηγορία", all_cat, default=all_cat, key="cat")

    df_c    = df_g[df_g["Κατηγορία"].isin(sel_cat)] if sel_cat else df_g
    all_sub = nonempty_sorted(df_c["Υποκατηγορία"])
    sel_sub = st.multiselect("Υποκατηγορία", all_sub, default=all_sub, key="sub")

    st.divider()
    if st.button("\U0001f504 Καθαρισμός φίλτρων"):
        for k in ["fam", "grp", "cat", "sub"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_fam: df = df[df["Οικογένεια"].isin(sel_fam)]
if sel_grp: df = df[df["Ομάδα"].isin(sel_grp)]
if sel_cat: df = df[df["Κατηγορία"].isin(sel_cat)]
if sel_sub: df = df[df["Υποκατηγορία"].isin(sel_sub)]

if df.empty:
    st.warning("⚠️ Δεν υπάρχουν δεδομένα με τα επιλεγμένα φίλτρα.")
    st.stop()

years     = sorted(df["Έτος"].unique().tolist())
years_str = [str(y) for y in years]
last      = years[-1] if years else None
prev      = years[-2] if len(years) >= 2 else None

# ─────────────────────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📌 KPIs — {}".format(period_lbl))

ll     = df[df["Like to Like"] == "L/L"]
kpi    = df.groupby("Έτος").agg(tz=("Τζίρος","sum"), qty=("Συν.ποσ.πωλήσεων","sum"))
kpi_ll = ll.groupby("Έτος").agg(tz=("Τζίρος","sum"), qty=("Συν.ποσ.πωλήσεων","sum"))
avg_s  = calc_avg_price(df)

def get(series_or_df, year, col=None):
    """Safe get from Series or DataFrame."""
    try:
        val = series_or_df.loc[year] if col is None else series_or_df.loc[year, col]
        return float(val)
    except Exception:
        return np.nan

if last:
    st.markdown("**Τζίρος (€)**")
    c1, c2, c3 = st.columns(3)
    c1.metric("L/L", fmt_eur(get(kpi_ll, last, "tz")),
              delta=delta_str(get(kpi_ll, last, "tz"), get(kpi_ll, prev, "tz")) if prev else None,
              help="Τζίρος L/L καταστημάτων")
    c2.metric("Σύνολο Δικτύου", fmt_eur(get(kpi, last, "tz")),
              delta=delta_str(get(kpi, last, "tz"), get(kpi, prev, "tz")) if prev else None)
    v_avg = get(avg_s, last)
    c3.metric("Μέση Τιμή", "€{:.2f}".format(v_avg) if not np.isnan(v_avg) else "—",
              delta=delta_str(v_avg, get(avg_s, prev)) if prev else None)

    st.markdown("**Τεμάχια**")
    d1, d2, _ = st.columns(3)
    d1.metric("L/L", fmt_qty(get(kpi_ll, last, "qty")),
              delta=delta_str(get(kpi_ll, last, "qty"), get(kpi_ll, prev, "qty")) if prev else None)
    d2.metric("Σύνολο Δικτύου", fmt_qty(get(kpi, last, "qty")),
              delta=delta_str(get(kpi, last, "qty"), get(kpi, prev, "qty")) if prev else None)

    if prev:
        st.caption("Δέλτα % vs {}".format(prev))

# ─────────────────────────────────────────────────────────────────────────────
# ΕΞΕΛΙΞΗ ΑΝΑ ΧΡΟΝΙΑ
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Εξέλιξη ανά Έτος")

t1, t2, t3 = st.tabs(["Τζίρος", "Τεμάχια", "Μέση Τιμή"])

with t1:
    fig = go.Figure()
    fig.add_trace(go.Bar(name="L/L", x=years_str,
                         y=[get(kpi_ll, y, "tz") for y in years], marker_color=COLORS[0]))
    fig.add_trace(go.Bar(name="Σύνολο", x=years_str,
                         y=[get(kpi, y, "tz") for y in years], marker_color=COLORS[1]))
    fig.update_layout(barmode="group", template="plotly_white",
                      xaxis_title="Έτος", yaxis_title="Τζίρος (€)",
                      legend=dict(orientation="h", y=1.12), height=380)
    st.plotly_chart(fig, use_container_width=True)

with t2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="L/L", x=years_str,
                          y=[get(kpi_ll, y, "qty") for y in years], marker_color=COLORS[2]))
    fig2.add_trace(go.Bar(name="Σύνολο", x=years_str,
                          y=[get(kpi, y, "qty") for y in years], marker_color=COLORS[3]))
    fig2.update_layout(barmode="group", template="plotly_white",
                       xaxis_title="Έτος", yaxis_title="Τεμάχια",
                       legend=dict(orientation="h", y=1.12), height=380)
    st.plotly_chart(fig2, use_container_width=True)

with t3:
    avg_vals = [get(avg_s, y) for y in years]
    fig3 = px.line(x=years_str, y=avg_vals, markers=True,
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

ch = (
    df.groupby(["Έτος", "Ομάδα Υποκ/των"])
      .agg(Τζίρος=("Τζίρος","sum"), Τεμάχια=("Συν.ποσ.πωλήσεων","sum"))
      .reset_index()
)
ch = ch[ch["Ομάδα Υποκ/των"].str.strip() != ""]
ch["Έτος"] = ch["Έτος"].astype(str)

ch1, ch2 = st.tabs(["Τζίρος ανά Κανάλι", "Τεμάχια ανά Κανάλι"])
for tab, metric, ylabel in [(ch1, "Τζίρος", "Τζίρος (€)"), (ch2, "Τεμάχια", "Τεμάχια")]:
    with tab:
        st.plotly_chart(bar_chart(ch, "Ομάδα Υποκ/των", metric, ylabel),
                        use_container_width=True)
        with st.expander("📋 Πίνακας"):
            pv = ch.pivot(index="Ομάδα Υποκ/των", columns="Έτος", values=metric).fillna(0).astype(int)
            st.dataframe(pv.style.format("{:,}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΑΝΑΛΥΣΗ ΑΝΑ ΚΑΤΗΓΟΡΙΑ
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🗂️ Ανάλυση ανά Κατηγορία")

LEVELS = ["Οικογένεια", "Ομάδα", "Κατηγορία", "Υποκατηγορία"]
ltabs  = st.tabs(LEVELS)

for lev, ltab in zip(LEVELS, ltabs):
    with ltab:
        agg = (
            df.groupby(["Έτος", lev])
              .agg(Τζίρος=("Τζίρος","sum"), Τεμάχια=("Συν.ποσ.πωλήσεων","sum"))
              .reset_index()
        )
        agg = agg[agg[lev].str.strip() != ""]
        agg["Έτος"] = agg["Έτος"].astype(str)

        if agg.empty:
            st.info("Δεν υπάρχουν δεδομένα.")
            continue

        in1, in2 = st.tabs(["Τζίρος", "Τεμάχια"])
        for inner, metric, ylabel in [(in1, "Τζίρος", "Τζίρος (€)"), (in2, "Τεμάχια", "Τεμάχια")]:
            with inner:
                st.plotly_chart(bar_chart(agg, lev, metric, ylabel),
                                use_container_width=True)
                with st.expander("📋 Πίνακας"):
                    pv = agg.pivot(index=lev, columns="Έτος", values=metric).fillna(0).astype(int)
                    st.dataframe(pv.style.format("{:,}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Sell-Out Dashboard · Φίλτρα: Οικογένεια → Ομάδα → Κατηγορία → Υποκατηγορία")
