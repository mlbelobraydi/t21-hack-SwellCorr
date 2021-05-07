import streamlit as st
from welly import Well, Project
from pathlib import Path
import plotly.express as px
import matplotlib.pyplot as plt
from striplog import Striplog, Legend
import helper
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.plotting import figure
import pandas as pd
from streamlit_bokeh_events import streamlit_bokeh_events
import xsection as xs

st.set_page_config(layout='wide')


def update_figure(picks, curve, active_well):
    """redraw the plot when the data in tops-storage is updated"""
    w = p.get_well(active_well)  ##selects the correct welly.Well object
    picks_df = pd.read_json(picks)
    for i, row in picks_df.iterrows():
        print(row.UWI, row.PICK, row.MD)
    print('***Active Well', active_well)
    picks_selected = picks_df[picks_df['UWI'] == active_well.replace(' ', '-')]
    print('***\n***\n***', picks_selected)
    
    # regenerate figure with the new horizontal line
    fig = px.line(x=w.data[curve], y=w.data[curve].basis, labels={'x': curve, 'y': 'MD'})
    
    fig.layout = {
        'uirevision': curve}  # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
    fig.update_yaxes(autorange="reversed")
    fig.layout.xaxis.fixedrange = True
    fig.layout.template = 'plotly_white'
    helper.update_picks_on_plot(fig, picks_selected)

    return fig

base_dir = "./data/Poseidon_data"

# # load well data
"""Need to add a method for the user to point to the directory or add additional las files later"""
fpath = Path(base_dir+"/las/*.LAS")
p = Project.from_las(str(fpath))
well_uwi = [w.uwi for w in p]
legend = Legend.from_csv(filename='data/Poseidon_data/tops_legend.csv') # direct link to specific data

for w in p:
    name = Path(w.fname).stem
    strip = Striplog.from_csv(base_dir+f'/tops/{name}.csv')
    w.data['tops'] = strip

well_uwi = [w.uwi for w in p]
well_uwi = st.sidebar.selectbox("Well Names", well_uwi)

df = p[0].df() ##gets data from the first well in the Welly Project
curve_list = df.columns.tolist() ##gets the column names for later use in the curve-selector tool
curve_dropdown_options = [{'label': k, 'value': k} for k in sorted(curve_list)] ##list of well log curves to the dropdown

curve = st.sidebar.selectbox("Well Names", [item['value'] for item in curve_dropdown_options])

# draw the initial plot
fig_well_1 = px.line(x=df[curve], y=df.index, labels = {'x':curve, 'y': df.index.name}) ##polot data and axis lables
fig_well_1.update_yaxes(autorange="reversed") ## flips the y-axis to increase down assuming depth increases
fig_well_1.layout.xaxis.fixedrange = True ##forces the x axis to a fixed range based on the curve data
fig_well_1.layout.template = 'plotly_white' ##template for the plotly figure

surface_picks_df = xs.get_tops_df(p)

tops_storage = surface_picks_df.to_json()
wells_tops = pd.read_json(tops_storage)
well_tops = wells_tops[wells_tops.UWI == well_uwi]
csv_txt = xs.df_to_csvtxt(well_tops)
p.get_well(well_uwi).data['tops'] = Striplog.from_csv(text=csv_txt)

fig = xs.section_plot(p, legend)

col1, col2 = st.beta_columns((1, 2))

fig_well_1 = update_figure(tops_storage, curve, well_uwi)

with col1:
    st.plotly_chart(fig_well_1, use_container_width=True)

with col2:
    st.pyplot(fig=fig)


def data(df):
    df = pd.DataFrame({"x": df[curve], "y": df.index})
    return df

df = data(df)
source = ColumnDataSource(df)

st.subheader("Select Points From Map")

plot = figure( tools="tap,lasso_select,reset", width=250, height=750)
plot.scatter(x="x", y="y", size=5, source=source, alpha=0.6)

source.selected.js_on_change(
    "indices",
    CustomJS(
        args=dict(source=source),
        code="""
        console.log(cb_obj);
        document.dispatchEvent(
            new CustomEvent("TestSelectEvent", {detail: {indices: cb_obj.indices}})
        )
    """,
    ),
)

event_result = streamlit_bokeh_events(
    events="TestSelectEvent",
    bokeh_plot=plot,
    key="foo",
    debounce_time=100,
    refresh_on_update=False
)

# some event was thrown
if event_result is not None:
    # TestSelectEvent was thrown
    print(event_result)
    if "TestSelectEvent" in event_result:
        st.subheader("Selected Points' Pandas Stat summary")
        indices = event_result["TestSelectEvent"].get("indices", [])
        st.table(df.iloc[indices].describe())

st.subheader("Raw Event Data")
st.write(event_result)
