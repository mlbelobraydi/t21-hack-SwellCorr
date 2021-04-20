import streamlit as st
from welly import Project
from pathlib import Path
import plotly.express as px
import matplotlib.pyplot as plt
from striplog import Striplog
import helper
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.plotting import figure
import pandas as pd
from streamlit_bokeh_events import streamlit_bokeh_events


st.set_page_config(layout='wide')


def get_tops_df(project, tops_field='tops', columns=['UWI', 'PICK', 'MD']):
    """
    Returns a DataFrame of tops from a welly Project
    """
    tops_set = []
    rows = []
    for well in project:
        for t in well.data[tops_field]:
            row = [well.uwi, t.components[0]['formation'], t.top.middle]
            tops_set.append(t.components[0]['formation'])
            rows.append(row)
    df = pd.DataFrame(rows, columns=columns)
    return df


def df_to_csvtxt(df, out_fields = ['top', 'Comp formation']):
    """
    This take a DataFram (df) for a well, and converts it into
    as csv-like string to make a Striplog
    """
    header = 'top, Comp formation\n'
    csv_txt = ''
    csv_txt += csv_txt + header
    for i, row in df.iterrows():
        csv_txt = csv_txt + str(row['MD']) + ', ' + row['PICK'] + '\n'
    return csv_txt


def plot_tops(ax, striplog, ymin=0, ymax=1e6, legend=None, field=None, **kwargs):
    """
    Plotting, but only for tops (as opposed to intervals).
    """
    if field is None:
        raise StriplogError('You must provide a field to plot.')

    ys = [iv.top.z for iv in striplog]

    try:
        try:
            ts = [getattr(iv.primary, field) for iv in striplog]
        except:
            ts = [iv.data.get(field) for iv in striplog]
    except:
        print('Could not find field')
        # raise StriplogError('Could not retrieve field.')

    for y, t in zip(ys, ts):
        if (y > ymin) and (y < ymax):
            ax.axhline(y, color='lightblue', lw=3, zorder=0)
            ax.text(0.1, y,  # -max(ys)/200,
                    t, fontsize=10, ha='left', va='center', bbox=dict(facecolor='white',
                                                                      edgecolor='grey',
                                                                      boxstyle='round',
                                                                      alpha=0.75))
    return


def section_plot(p, legend=None, ymin=3000, ymax=5500):
    fig = plt.figure(constrained_layout=True, figsize=(6, 10))
    axes_names = [name.replace(' ', '-') for name in p.uwis]
    ax_dict = fig.subplot_mosaic([axes_names])
    for i, w in enumerate(p):
        print("plotting", w)
        name = w.uwi.replace(' ', '-')
        w.data['tops'].plot(ax=ax_dict[w.uwi.replace(' ', '-')], legend=legend, alpha=0.5)
        plot_tops(ax_dict[name], w.data['tops'], field='formation', ymin=ymin, ymax=ymax)
        ax_dict[name].plot(w.data['GR'] / 120, w.data['GR'].basis, c='k', lw=0.5)
        ax_dict[name].set_xlim(0, 175 / 120)
        ax_dict[name].set_ylim(ymax, ymin)
        ax_dict[name].set_title(name)
        if i != 0:
            ax_dict[name].set_yticklabels([])

    #fig.savefig('cross_section.png')
    return fig


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

for w in p:
    name = w.fname.split('/')[-1].split('.')[0]
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

surface_picks_df = get_tops_df(p)

tops_storage = surface_picks_df.to_json()
wells_tops = pd.read_json(tops_storage)
well_tops = wells_tops[wells_tops.UWI == well_uwi]
csv_txt = df_to_csvtxt(well_tops)
p.get_well(well_uwi).data['tops'] = Striplog.from_csv(text=csv_txt)

fig = section_plot(p)

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
