import streamlit as st
import pandas as pd
import numpy as np
import os, shutil, time, xlwings as xw
import streamlit.components.v1 as components
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.charts import Line
 
 
# File paths
ORIGINAL_FILE = "original.xlsx"
WORKING_FILE  = "working.xlsx"
 
# Create the copy if it doesn't exist
if not os.path.exists(WORKING_FILE):
    shutil.copy(ORIGINAL_FILE, WORKING_FILE)
 
# Load data from the working File 
def load_data(file_path):
    return pd.read_excel(file_path, header=0)
 
if "original_df" not in st.session_state:
    st.session_state.original_df = load_data(ORIGINAL_FILE)
    st.session_state.modified_df = load_data(WORKING_FILE)
    st.session_state.recent_changes = []
 
df = st.session_state.modified_df
original_df = st.session_state.original_df.copy()
 

# Excel row numbers:
EXCEL_ROW = 125
DF_ROW    = EXCEL_ROW - 2
 
if DF_ROW >= df.shape[0]:
    st.error(f"DataFrame has {df.shape[0]} rows; row {DF_ROW} does not exist.")
    st.stop()
 
# Interface metrics & mapping excel columns
metrics = [
    "Pell graduation rates", "Graduation rates", "Borrower debt", "First-year retention rates",
    "Citations per publication", "College grads earning more than a high school grad",
    "Pell graduation performance", "Financial resources per student", "Field weighted citations",
    "Full-time faculty", "Graduation rate performance", "Peer assessment",
    "Citations in top 25% journals", "Citations in top 5% journals", "Student-faculty ratio",
    "Faculty salaries", "Average Standardized Tests Score"
]
 
col_map = {
    "Pell graduation rates": "D",
    "Graduation rates": "G",
    "Borrower debt": "H",
    "First-year retention rates": "I",
    "Citations per publication": "J",
    "College grads earning more than a high school grad": "K",
    "Pell graduation performance": "L",
    "Financial resources per student": "M",
    "Field weighted citations": "N",
    "Full-time faculty": "O",
    "Graduation rate performance": "P",
    "Peer assessment": "T",
    "Citations in top 25% journals": "U",
    "Citations in top 5% journals": "V",
    "Student-faculty ratio": "AA",
    "Faculty salaries": "AB",
    "Average Standardized Tests Score": "AC"
}
 
 
# Top header and rank circles 
st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>Creighton Ranking Simulator</h1>", unsafe_allow_html=True)
 

adjusted_rank_value = df.at[DF_ROW, "Excel Rank"]
 
 
 
 
FIXED_2025_RANK = 121
PREDICTED_RANK  = 116

#HTML Part
 
html_code = f"""
<html>
<head>
<style>
  .circle-container {{
      display: flex;
      justify-content: center;
      gap: 80px;
      align-items: flex-start;
  }}
  .circle-block {{
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 140px;
  }}
  .circle-label {{
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 15px;
      font-family: 'Segoe UI', sans-serif;
      text-align: center;
  }}
  .circle {{
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background: transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      font-weight: bold;
      color: #00308F;
      border: 3px solid black;
      font-family: 'Segoe UI', sans-serif;
  }}
</style>
</head>
<body>
<div class="circle-container">
<div class="circle-block">
<div class="circle-label">2025 ACTUAL RANK</div>
<div class="circle">121</div>
</div>
<div class="circle-block">
<div class="circle-label">2026 PREDICTED RANK</div>
<div class="circle">122</div>
</div>
<div class="circle-block">
<div class="circle-label">SIMULATED RANK</div>
<div class="circle">{int(adjusted_rank_value) if adjusted_rank_value is not None else 'N/A'}</div>
</div>
</div>
</body>
</html>
"""
components.html(html_code, height=250)

#Instruction 

st.markdown("""
<div style="max-width:800px; margin:20px auto; padding:20px;
            border:2px solid #00308F; border-radius:8px;
            font-family:'Segoe UI',sans-serif; background:#fff;">
<h4 style="text-align:center; margin-top:0;">How to Use the Simulator</h4>
<ol style="margin-left:1em;">
<li>Adjust the metric values in the table below.</li>
<li>Press "Enter" or click outside the fields to save your changes.</li>
<li>Scroll down to the bottom to view the saved changes.</li>
<li>Click " 💾 Save Changes" to recalculate the simulated rank after making all necessary adjustments.</li>
<li>A green message will appear when the new simulated rank is ready.</li>
<li>Scroll up to the top to view the updated simulated rank.</li>
<li>Click "🔄 Reset Metrics" to revert to the original values.</li>
<p>If your web browser is in "dark" theme, please switch to the "light" theme by click the "Three Dots Icon > Settings > Appearance > Theme > Light.</p>
</ol>
</div>
""", unsafe_allow_html=True)


# Metrics table title
st.markdown("<h3 style='text-align: center; margin-bottom: 15px;'>US News Weighted Metrics</h3>", unsafe_allow_html=True)


# Center reset button
reset_col1, reset_col2, reset_col3 = st.columns([3, 2, 3])
with reset_col2:
    if st.button("🔄 Reset Metrics"):
        shutil.copy(ORIGINAL_FILE, WORKING_FILE)
        st.session_state.modified_df = load_data(WORKING_FILE)
        st.session_state.recent_changes = []
        st.rerun()

st.session_state.recent_changes = []
for metric in metrics:
    try:
        current_value = float(st.session_state.modified_df.at[DF_ROW, metric])
        original_value = float(st.session_state.original_df.at[DF_ROW, metric])
    except Exception as e:
        st.error(f"Error reading '{metric}' from row {DF_ROW}: {e}")
        current_value = 0.0
        original_value = 0.0
 
    if metric in ["Borrower debt", "Financial resources per student"]:
        str_current = f"{current_value:.5f}"
    else:
        str_current = f"{current_value:.2f}"
 
    user_input = st.text_input(metric, value=str_current)
 
    try:
        new_value = float(user_input)
    except ValueError:
        new_value = current_value
 
    if abs(new_value - current_value) > 1e-9:
        st.session_state.modified_df.at[DF_ROW, metric] = new_value
 
    # Track changes compared to original
    if abs(new_value - original_value) > 1e-9:
        st.session_state.recent_changes.append(
            f"🔧 {metric} changed from {original_value} to {new_value}."
        )
 
# Summary of Changes
if st.session_state.recent_changes:
    st.markdown("<h4 style='margin-top: 30px;'>📝 Recent Changes:</h4>", unsafe_allow_html=True)
    for change in st.session_state.recent_changes:
        st.markdown(f"- {change}")


# Excel Rewrite 
def update_excel_and_get_rank():
    app = None
    try:
        app = xw.App(visible=False)
        wb = xw.Book(WORKING_FILE)
        sht = wb.sheets[0]
        # Write updated metrics to the working file
        for metric in metrics:
            new_val = st.session_state.modified_df.at[DF_ROW, metric]
            excel_col = col_map[metric]
            sht.range(f"{excel_col}{EXCEL_ROW}").value = new_val
 
        wb.api.Application.CalculateFullRebuild()
        time.sleep(3)
        updated_rank = sht.range(f"BO{EXCEL_ROW}").value
        wb.save()
        wb.close()
        return updated_rank
    except Exception as e:
        st.error("Error during Excel update: " + str(e))
        return None
    finally:
        if app is not None:
            try:
                app.quit()
            except Exception:
                pass
 

# Centered save changes button
save_col1, save_col2, save_col3 = st.columns([3, 2, 3])
with save_col2:
    if st.button("💾 Save Changes"):
        new_rank = update_excel_and_get_rank()
        st.success(f"Saved changes. New Adjusted Rank: {new_rank}")
        st.session_state.modified_df = load_data(WORKING_FILE)
        st.rerun()
 
# Insights section
st.markdown("")
st.markdown("")
st.markdown("")

st.markdown("<h3 style='text-align:center; margin-top:30px;'>Insight Section</h3>", unsafe_allow_html=True)
st.write("This section shows Creighton's ranking from 2023 to the predicted rank for 2026, along with four" \
" other key US metrics that significantly impact rank performance, supported by bar graphs.")

 
# X-axis labels
x_data = ["2023", "2024", "2025", "Predicted 2026"]
y_data = [121, 124, 121, 116]
 
line_chart = (
    Line(init_opts=opts.InitOpts(width="650px", height="400px"))
    .add_xaxis(x_data)
    .add_yaxis(
        series_name="Creighton's Rank",
        y_axis=y_data,
        label_opts=opts.LabelOpts(is_show=True),
        is_smooth=True,
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="Creighton's Rank",
            subtitle="2023, 2024, 2025, & 2026",
            pos_top="0%",      
            pos_left="center", 
        ),
       
        legend_opts=opts.LegendOpts(
            pos_top="15%",   
            pos_left="center"
        ),
        tooltip_opts=opts.TooltipOpts(is_show=True),
        yaxis_opts=opts.AxisOpts(
            is_inverse=True,
            min_=110,
            max_=130,
            interval=2
        ),
    )
)
 
chart_html = line_chart.render_embed()
st.components.v1.html(chart_html, height=400)
 

#Side by side 2 bar graphs 
row1_col1, row1_col2 = st.columns(2, gap="large")
 
with row1_col1:
    bar1 = (
       
        Bar(init_opts=opts.InitOpts(width="280px", height="220px"))
          .add_xaxis(["2024", "2025"])
          .add_yaxis("", [88, 92], category_gap="50%")
          .set_global_opts(
              title_opts=opts.TitleOpts(title="College vs. HS Earnings", pos_top="5%"),
              xaxis_opts=opts.AxisOpts(
                  axislabel_opts=opts.LabelOpts(font_size=12),
                  axistick_opts=opts.AxisTickOpts(is_align_with_label=True)
              ),
              yaxis_opts=opts.AxisOpts(min_=80, max_=100, axislabel_opts=opts.LabelOpts(font_size=12)),
              legend_opts=opts.LegendOpts(is_show=False),
              tooltip_opts=opts.TooltipOpts(is_show=True),
          )
    )
    st.components.v1.html(bar1.render_embed(), height=240)
 
 
with row1_col2:
    bar2 = (
        Bar(init_opts=opts.InitOpts(width="280px", height="220px"))
          .add_xaxis(["2024", "2025"])
          .add_yaxis("", [11.8, 10.1], category_gap="50%")
          .set_global_opts(
              title_opts=opts.TitleOpts(title="Student-Faculty Ratio", pos_top="5%"),
              xaxis_opts=opts.AxisOpts(
                  axislabel_opts=opts.LabelOpts(font_size=12),
                  axistick_opts=opts.AxisTickOpts(is_align_with_label=True)
              ),
              yaxis_opts=opts.AxisOpts(min_=0, max_=15, axislabel_opts=opts.LabelOpts(font_size=12)),
              legend_opts=opts.LegendOpts(is_show=False),
              tooltip_opts=opts.TooltipOpts(is_show=True),
          )
    )
    st.components.v1.html(bar2.render_embed(), height=240)
 
#Side by side 2 bar graphs
row2_col1, row2_col2 = st.columns(2, gap="large")
 
with row2_col1:
    bar3 = (
        Bar(init_opts=opts.InitOpts(width="280px", height="220px"))
          .add_xaxis(["2024", "2025"])
          .add_yaxis("", [91.25, 91.75], category_gap="50%")
          .set_global_opts(
              title_opts=opts.TitleOpts(title="First Year Retention Rates", pos_top="5%"),
              xaxis_opts=opts.AxisOpts(
                  axislabel_opts=opts.LabelOpts(font_size=12),
                  axistick_opts=opts.AxisTickOpts(is_align_with_label=True)
              ),
              yaxis_opts=opts.AxisOpts(min_=90, max_=95, axislabel_opts=opts.LabelOpts(font_size=12)),
              legend_opts=opts.LegendOpts(is_show=False),
              tooltip_opts=opts.TooltipOpts(is_show=True),
          )
    )
    st.components.v1.html(bar3.render_embed(), height=240)
 
with row2_col2:
    bar4 = (
        Bar(init_opts=opts.InitOpts(width="280px", height="220px"))
          .add_xaxis(["2024", "2025"])
          .add_yaxis("", [78.25, 78.75], category_gap="50%")
          .set_global_opts(
              title_opts=opts.TitleOpts(title="Graduation Rates", pos_top="5%"),
              xaxis_opts=opts.AxisOpts(
                  axislabel_opts=opts.LabelOpts(font_size=12),
                  axistick_opts=opts.AxisTickOpts(is_align_with_label=True)
              ),
              yaxis_opts=opts.AxisOpts(min_=75, max_=80, axislabel_opts=opts.LabelOpts(font_size=12)),
              legend_opts=opts.LegendOpts(is_show=False),
              tooltip_opts=opts.TooltipOpts(is_show=True),
          )
    )
    st.components.v1.html(bar4.render_embed(), height=240)


# Summary section 
st.markdown("<h3 style='text-align:center; margin-top:-40px;'>Summary</h3>", unsafe_allow_html=True)

 
summary_box = """
<div style="max-width:650px; margin:0 auto; border:1px solid black; padding:15px; background-color:white; border-radius:5px;">
<ul>
<li><strong>College vs High School Earnings</strong>: Earnings increased from  <strong>$88K</strong> in 2024 to <strong>$92k</strong> in 2025, reflecting a growth of <strong>$4k</strong>.</li>
<li><strong>Student–Faculty Ratio</strong>: The ratio improved from <strong>11.8</strong> in 2024 to <strong>10.1</strong> in 2025, showing an improvement in faculty availability per student.</li>
<li><strong>First-Year Retention Rates</strong>: The retention rates rose slightly from <strong>91.25%</strong> in 2024 to <strong>91.75%</strong> in 2025, indicating a positive trend in student retention.</li>
<li><strong>Graduation Rates</strong>: The graduation rate climbed from <strong>78.25%</strong> in 2024 to <strong>78.75%</strong> in 2025, marking a modest improvement in graduation success.</li>
</ul>
</div>
"""
st.markdown(summary_box, unsafe_allow_html=True)