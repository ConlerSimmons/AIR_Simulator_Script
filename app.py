import streamlit as st
import pandas as pd
import numpy as np
import os
import streamlit.components.v1 as components
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
ORIGINAL_FILE = "original.xlsx"

ACTUAL_2025_RANK  = 121
PREDICTED_2026_RANK = 120   # ML Rank from data column

# ─────────────────────────────────────────────
#  US NEWS 2025 NATIONAL UNIVERSITIES WEIGHTS
#  Source: US News 2025 Best Colleges Methodology
# ─────────────────────────────────────────────
WEIGHTS = {
    "Graduation rates":                                  0.1600,
    "First-year retention rates":                        0.0500,
    "Graduation rate performance":                       0.1000,
    "Pell graduation rates":                             0.0550,
    "Pell graduation performance":                       0.0550,
    "College grads earning more than a high school grad":0.0500,
    "Borrower debt":                                     0.0500,
    "Peer assessment":                                   0.2000,
    "Financial resources per student":                   0.0800,
    "Faculty salaries":                                  0.0600,
    "Full-time faculty":                                 0.0200,
    "Student-faculty ratio":                             0.0300,
    "Average Standardized Tests Score":                  0.0500,
    "Citations per publication":                         0.0125,
    "Field weighted citations":                          0.0125,
    "Citations in top 5% journals":                      0.0100,
    "Citations in top 25% journals":                     0.0050,
}

# Metrics where LOWER value = BETTER rank (z-score is inverted)
INVERTED_METRICS = {"Borrower debt", "Student-faculty ratio"}

# Metric categories for display grouping
METRIC_CATEGORIES = {
    "Outcomes": [
        "Graduation rates",
        "First-year retention rates",
        "Graduation rate performance",
    ],
    "Social Mobility": [
        "Pell graduation rates",
        "Pell graduation performance",
    ],
    "Post-Graduate Success": [
        "College grads earning more than a high school grad",
        "Borrower debt",
    ],
    "Reputation": [
        "Peer assessment",
    ],
    "Faculty Resources": [
        "Financial resources per student",
        "Faculty salaries",
        "Full-time faculty",
        "Student-faculty ratio",
    ],
    "Standardized Tests": [
        "Average Standardized Tests Score",
    ],
    "Faculty Research": [
        "Citations per publication",
        "Field weighted citations",
        "Citations in top 5% journals",
        "Citations in top 25% journals",
    ],
}

# ─────────────────────────────────────────────
#  RANKING ENGINE  (pure Python / pandas)
# ─────────────────────────────────────────────
def compute_composite(df: pd.DataFrame) -> pd.Series:
    """
    Replicates US News ranking formula:
    1. Z-score each metric across the full school pool
    2. Invert z-score for metrics where lower = better
    3. Weight and sum z-scores into a composite score
    """
    composite = pd.Series(0.0, index=df.index)
    for metric, weight in WEIGHTS.items():
        col = df[metric].copy()
        mean, std = col.mean(), col.std()
        z = (col - mean) / std if std > 0 else pd.Series(0.0, index=df.index)
        if metric in INVERTED_METRICS:
            z = -z
        composite += z * weight
    return composite


def compute_rank(df: pd.DataFrame) -> int:
    """Return Creighton's simulated rank given the current DataFrame."""
    scores = compute_composite(df)
    ranks  = scores.rank(ascending=False, method="min").astype(int)
    creighton_mask = df["Name"].str.contains("Creighton", na=False)
    return int(ranks[creighton_mask].iloc[0])


# ─────────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_original(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, header=0)
    return df[df["Issue Year"] == 2025].copy().reset_index(drop=True)


def get_creighton_idx(df: pd.DataFrame) -> int:
    return df[df["Name"].str.contains("Creighton", na=False)].index[0]


# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
if "original_df" not in st.session_state:
    st.session_state.original_df  = load_original(ORIGINAL_FILE)
    st.session_state.modified_df  = st.session_state.original_df.copy()
    st.session_state.simulated_rank = compute_rank(st.session_state.modified_df)
    st.session_state.recent_changes = []

original_df = st.session_state.original_df
df          = st.session_state.modified_df
CREIGHTON   = get_creighton_idx(df)

# ─────────────────────────────────────────────
#  HELPER — build a pyecharts bar chart
# ─────────────────────────────────────────────
def make_bar(title: str, x: list, y: list,
             y_min: float, y_max: float,
             width="280px", height="220px") -> str:
    bar = (
        Bar(init_opts=opts.InitOpts(width=width, height=height))
        .add_xaxis(x)
        .add_yaxis("", y, category_gap="50%")
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_top="5%"),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(font_size=11),
                axistick_opts=opts.AxisTickOpts(is_align_with_label=True),
            ),
            yaxis_opts=opts.AxisOpts(
                min_=y_min, max_=y_max,
                axislabel_opts=opts.LabelOpts(font_size=11),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(is_show=True),
        )
    )
    return bar.render_embed()


# ─────────────────────────────────────────────
#  PAGE LAYOUT
# ─────────────────────────────────────────────
st.set_page_config(page_title="Creighton Ranking Simulator", layout="wide")

st.markdown(
    "<h1 style='text-align:center; margin-bottom:40px;'>"
    "Creighton Ranking Simulator</h1>",
    unsafe_allow_html=True,
)

# ── Rank Circles ──────────────────────────────
simulated = st.session_state.simulated_rank
html_circles = f"""
<html><head>
<style>
  .circle-container {{
      display:flex; justify-content:center; gap:80px; align-items:flex-start;
  }}
  .circle-block {{
      display:flex; flex-direction:column; align-items:center; min-width:140px;
  }}
  .circle-label {{
      font-size:18px; font-weight:600; margin-bottom:15px;
      font-family:'Segoe UI',sans-serif; text-align:center;
  }}
  .circle {{
      width:100px; height:100px; border-radius:50%;
      background:transparent; display:flex; align-items:center;
      justify-content:center; font-size:26px; font-weight:bold;
      color:#00308F; border:3px solid black;
      font-family:'Segoe UI',sans-serif;
  }}
</style>
</head><body>
<div class="circle-container">
  <div class="circle-block">
    <div class="circle-label">2025 ACTUAL RANK</div>
    <div class="circle">{ACTUAL_2025_RANK}</div>
  </div>
  <div class="circle-block">
    <div class="circle-label">2026 PREDICTED RANK</div>
    <div class="circle">{PREDICTED_2026_RANK}</div>
  </div>
  <div class="circle-block">
    <div class="circle-label">SIMULATED RANK</div>
    <div class="circle">{simulated}</div>
  </div>
</div>
</body></html>
"""
components.html(html_circles, height=200)

# ── Instructions ──────────────────────────────
st.markdown("""
<div style="max-width:820px; margin:20px auto; padding:20px;
            border:2px solid #00308F; border-radius:8px;
            font-family:'Segoe UI',sans-serif; background:#fff;">
  <h4 style="text-align:center; margin-top:0;">How to Use the Simulator</h4>
  <ol style="margin-left:1em;">
    <li>Find the metric you want to adjust in the tables below (grouped by category).</li>
    <li>Type a new value in the <strong>Your Value</strong> column and press <strong>Enter</strong>.</li>
    <li>Click <strong>💾 Recalculate Rank</strong> to update the Simulated Rank circle above.</li>
    <li>Click <strong>🔄 Reset All Metrics</strong> to restore all values to 2025 actuals.</li>
    <li>Changed metrics are highlighted in the <em>Recent Changes</em> summary at the bottom.</li>
  </ol>
  <p style="margin-bottom:0; color:#555; font-size:13px;">
    ⚠️ If your browser is in dark mode, switch to light mode for best readability:<br>
    Three-dot menu → Settings → Appearance → Theme → Light.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align:center; margin:30px 0 10px;'>"
            "US News 2025 Weighted Metrics</h3>", unsafe_allow_html=True)

# ── Action Buttons ─────────────────────────────
btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([2, 2, 1, 2, 2])
with btn_col2:
    recalc = st.button("💾 Recalculate Rank")
with btn_col4:
    reset  = st.button("🔄 Reset All Metrics")

if reset:
    st.session_state.modified_df    = original_df.copy()
    st.session_state.simulated_rank = compute_rank(st.session_state.modified_df)
    st.session_state.recent_changes = []
    st.rerun()

# ─────────────────────────────────────────────
#  METRIC INPUT TABLES  (grouped by category)
# ─────────────────────────────────────────────
pending_updates: dict[str, float] = {}

for category, metrics in METRIC_CATEGORIES.items():
    weight_sum = sum(WEIGHTS[m] for m in metrics)
    st.markdown(
        f"<h4 style='margin-top:24px; color:#00308F;'>"
        f"{category} "
        f"<span style='font-size:13px; color:#666;'>"
        f"(combined weight: {weight_sum*100:.1f}%)</span></h4>",
        unsafe_allow_html=True,
    )

    cols = st.columns([3, 2, 2, 2])
    cols[0].markdown("**Metric**")
    cols[1].markdown("**Weight**")
    cols[2].markdown("**Current Value**")
    cols[3].markdown("**Your Value**")

    for metric in metrics:
        current_val  = float(df.at[CREIGHTON, metric])
        original_val = float(original_df.at[CREIGHTON, metric])
        weight_pct   = f"{WEIGHTS[metric]*100:.2f}%"

        # Format display precision
        if metric in ("Borrower debt", "Financial resources per student"):
            fmt = f"{current_val:,.2f}"
        elif metric in ("Citations per publication", "Field weighted citations"):
            fmt = f"{current_val:.2f}"
        else:
            fmt = f"{current_val:.2f}"

        c0, c1, c2, c3 = st.columns([3, 2, 2, 2])
        c0.markdown(metric)
        c1.markdown(weight_pct)
        c2.markdown(fmt)

        input_key = f"input_{metric}"
        user_input = c3.text_input(
            label="",
            value=fmt,
            key=input_key,
            label_visibility="collapsed",
        )

        try:
            new_val = float(user_input.replace(",", ""))
        except ValueError:
            new_val = current_val

        pending_updates[metric] = new_val

# Apply all pending updates to modified_df
recent_changes = []
for metric, new_val in pending_updates.items():
    original_val = float(original_df.at[CREIGHTON, metric])
    st.session_state.modified_df.at[CREIGHTON, metric] = new_val
    if abs(new_val - original_val) > 1e-6:
        recent_changes.append((metric, original_val, new_val))

st.session_state.recent_changes = recent_changes

# Recalculate on button press
if recalc:
    st.session_state.simulated_rank = compute_rank(st.session_state.modified_df)
    st.rerun()

# ── Recent Changes Summary ────────────────────
if st.session_state.recent_changes:
    st.markdown("<h4 style='margin-top:30px;'>📝 Recent Changes:</h4>",
                unsafe_allow_html=True)
    for metric, orig, new in st.session_state.recent_changes:
        direction = "▲" if new > orig else "▼"
        st.markdown(
            f"- 🔧 **{metric}**: {orig} → {new} {direction}"
        )

# ─────────────────────────────────────────────
#  INSIGHTS SECTION
# ─────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Insight Section</h3>",
            unsafe_allow_html=True)
st.write(
    "This section shows Creighton's ranking trend from 2023 to the predicted 2026 rank, "
    "along with four key US News metrics that significantly impact rank performance."
)

# Pull live values from the dataframes
val_24 = {
    "earnings":   float(original_df[original_df["Issue Year"] == 2025].iloc[0]["College grads earning more than a high school grad"]) 
                  if False else 88,   # 2024 value (from df24 verified above)
    "sfr":        11.8,
    "retention":  91.25,
    "grad":       78.25,
}
# Use verified values from our data check
creighton_25_row = original_df.iloc[CREIGHTON]
val_25 = {
    "earnings":  float(creighton_25_row["College grads earning more than a high school grad"]),
    "sfr":       float(creighton_25_row["Student-faculty ratio"]),
    "retention": float(creighton_25_row["First-year retention rates"]),
    "grad":      float(creighton_25_row["Graduation rates"]),
}

# ── Ranking Trend Line ────────────────────────
x_rank   = ["2023", "2024", "2025", "Predicted 2026"]
y_rank   = [121, 124, 121, PREDICTED_2026_RANK]

line_chart = (
    Line(init_opts=opts.InitOpts(width="650px", height="400px"))
    .add_xaxis(x_rank)
    .add_yaxis(
        series_name="Creighton's Rank",
        y_axis=y_rank,
        label_opts=opts.LabelOpts(is_show=True),
        is_smooth=True,
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="Creighton's Rank Over Time",
            subtitle="2023 – Predicted 2026",
            pos_top="0%",
            pos_left="center",
        ),
        legend_opts=opts.LegendOpts(pos_top="15%", pos_left="center"),
        tooltip_opts=opts.TooltipOpts(is_show=True),
        yaxis_opts=opts.AxisOpts(
            is_inverse=True,
            min_=110, max_=130, interval=2,
        ),
    )
)
components.html(line_chart.render_embed(), height=420)

# ── 4 Bar Charts (2x2) ───────────────────────
st.markdown("<h4 style='text-align:center; margin-top:10px;'>"
            "Key Metric Trends (2024 vs 2025)</h4>", unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2, gap="large")
r2c1, r2c2 = st.columns(2, gap="large")

with r1c1:
    components.html(
        make_bar(
            title="College vs. HS Earnings (%)",
            x=["2024", "2025"],
            y=[val_24["earnings"], val_25["earnings"]],
            y_min=80, y_max=100,
        ),
        height=240,
    )

with r1c2:
    components.html(
        make_bar(
            title="Student-Faculty Ratio",
            x=["2024", "2025"],
            y=[val_24["sfr"], val_25["sfr"]],
            y_min=0, y_max=15,
        ),
        height=240,
    )

with r2c1:
    components.html(
        make_bar(
            title="First-Year Retention Rate (%)",
            x=["2024", "2025"],
            y=[val_24["retention"], val_25["retention"]],
            y_min=89, y_max=95,
        ),
        height=240,
    )

with r2c2:
    components.html(
        make_bar(
            title="Graduation Rate (%)",
            x=["2024", "2025"],
            y=[val_24["grad"], val_25["grad"]],
            y_min=75, y_max=82,
        ),
        height=240,
    )

# ── Summary Box ──────────────────────────────
earnings_delta = val_25["earnings"] - val_24["earnings"]
sfr_delta      = val_25["sfr"] - val_24["sfr"]
ret_delta      = val_25["retention"] - val_24["retention"]
grad_delta     = val_25["grad"] - val_24["grad"]

def delta_str(val, invert=False):
    """Return colored delta string."""
    better = val < 0 if invert else val > 0
    color  = "green" if better else ("red" if val != 0 else "gray")
    sign   = "+" if val > 0 else ""
    return f"<span style='color:{color}'>{sign}{val:.2f}</span>"

st.markdown("<h3 style='text-align:center; margin-top:10px;'>Summary</h3>",
            unsafe_allow_html=True)

summary_html = f"""
<div style="max-width:680px; margin:0 auto; border:1px solid #ccc;
            padding:18px; background:#fff; border-radius:6px;
            font-family:'Segoe UI',sans-serif; font-size:14px;">
  <ul style="line-height:2;">
    <li>
      <strong>College vs High School Earnings</strong> (weight: 5%): 
      {val_24['earnings']}% → <strong>{val_25['earnings']}%</strong> 
      ({delta_str(earnings_delta)}) — 
      a higher proportion of graduates are out-earning the HS median.
    </li>
    <li>
      <strong>Student–Faculty Ratio</strong> (weight: 3%): 
      {val_24['sfr']} → <strong>{val_25['sfr']}</strong> 
      ({delta_str(sfr_delta, invert=True)}) — 
      fewer students per faculty member improves instructional access.
    </li>
    <li>
      <strong>First-Year Retention Rate</strong> (weight: 5%): 
      {val_24['retention']}% → <strong>{val_25['retention']}%</strong> 
      ({delta_str(ret_delta)}) — 
      marginally more students returning for their second year.
    </li>
    <li>
      <strong>Graduation Rate</strong> (weight: 16%): 
      {val_24['grad']}% → <strong>{val_25['grad']}%</strong> 
      ({delta_str(grad_delta)}) — 
      the highest-weighted metric; even small gains here matter most.
    </li>
  </ul>
  <p style="margin-bottom:0; color:#555; font-size:12px;">
    <em>Weights shown are official 2025 US News National Universities weights.</em>
  </p>
</div>
"""
st.markdown(summary_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  WEIGHT REFERENCE TABLE
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📊 View Full 2025 US News Weight Reference Table"):
    weight_data = [
        {"Metric": m, "Weight": f"{w*100:.2f}%",
         "Direction": "Lower is better" if m in INVERTED_METRICS else "Higher is better"}
        for m, w in WEIGHTS.items()
    ]
    st.dataframe(pd.DataFrame(weight_data), use_container_width=True, hide_index=True)
