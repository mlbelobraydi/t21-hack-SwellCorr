from welly import Well, Project ##Welly is used to organize the well data and project collection

import plotly.express as px ##plotly is used as the main display functionality
from dash import Dash, callback_context ##dash is used to update the plot and fields dynamically in a web browser
import dash_core_components as dcc
import dash_html_components as html
import flask
from dash.dependencies import Input, Output, State

import json
import numpy as np
import pandas as pd
from pathlib import Path
import numpy as np

import helper


app = Dash(__name__)
# Create server variable with Flask server object for use with gunicorn
server = app.server

# # load well data
"""Need to add a method for the user to point to the directory or add additional las files later"""
#w = Well.from_las(str(Path("well_picks/data/las/PoseidonNorth1Decim.LAS"))) #original example
p = Project.from_las(str(Path("well_picks/data/McMurray_data/las/*.LAS")))
well_uwi = [w.uwi for w in p] ##gets the well uwi data for use in the well-selector tool

df = p[0].df() ##gets data from the first well in the Welly Project
curve_list = df.columns.tolist() ##gets the column names for later use in the curve-selector tool
curve = curve_list[0] ##gets the first curve name to be used as the first curve displayed in the plotly figure

## Load well top data
surface_picks_df = pd.read_table(Path('./well_picks/data/McMurray_data/PICKS.TXT'),
                                usecols=['UWI', 'PICK', 'MD'])



#well dropdown selector
well_dropdown_options = [{'label': k, 'value': k} for k in sorted(well_uwi)] ##list of wells to the dropdown
#tops dropdown options
"""we need to have a stratigraphic column at some point"""
tops_dropdown_options = [{'label': k, 'value': k} for k in list(surface_picks_df['PICK'].unique())] ##list of tops to the dropdown
##well log curve dropdown options
curve_dropdown_options = [{'label': k, 'value': k} for k in sorted(curve_list)] ##list of well log curves to the dropdown

# draw the initial plot
fig_well_1 = px.line(x=df[curve], y=df.index, labels = {'x':curve, 'y': df.index.name}) ##polot data and axis lables
fig_well_1.update_yaxes(autorange="reversed") ## flips the y-axis to increase down assuming depth increases
fig_well_1.layout.xaxis.fixedrange = True ##forces the x axis to a fixed range based on the curve data
fig_well_1.layout.template = 'plotly_white' ##template for the plotly figure

app.title = "SwellCorr"
app.layout = html.Div(children=[
    html.Div(
        children=[
            html.H4('SwellCorr well correlation')
        ]
    ),
    html.Div(
        children=[
            html.Div([
                'Select well:', ##Well selector
                dcc.Dropdown(id='well-selector', options=well_dropdown_options, value=well_uwi[0], style={'width': '200px'}),

                'Edit tops:', ##existing top to edit selector
                dcc.Dropdown(id='top-selector', options=tops_dropdown_options, placeholder="Select a top to edit", style={'width': '200px'}),
                
                html.Hr(),
                'Create a new surface pick:', html.Br(), ##dialog to creat a new well top correlation for a well
                dcc.Input(id='new-top-name', placeholder='Name for new top', type='text', value=''),
                html.Button('Create', id='new-top-button'),
                
                html.Hr(),
                'Curve Select:', html.Br(), ##well log curve selector
                dcc.Dropdown(id='curve-selector', options=curve_dropdown_options, value=curve, placeholder="Select a curve", style={'width': '200px'}),
                
                html.Hr(),
                "Write tops to file:", ##input box and button for outputting well correlation results to file
                dcc.Input(id='input-save-path', type='text', placeholder='path_to_save_picks.json', value=''),
                html.Button('Save Tops', id='save-button', n_clicks=0),

                html.Hr(), ##button to update the Striplog dict on the page
                html.Button('Update Striplog', id='gen-striplog-button')

            ]),
            dcc.Graph(id="well_plot", 
                        figure=fig_well_1,
                        style={'width': '200', 'height':'1000px'}), ##figure of log curve with well tops

            html.Div([
                # hidden_div for storing tops data as json
                # Currently not hidden for debugging purposes. change style={'display': 'none'}
                html.Div(id='tops-storage', children=surface_picks_df.to_json()),#, style={'display': 'none'}),

                html.Hr(),
                html.H4('Striplog CSV Text:'),
                html.Pre(id='striplog-txt', children='', style={'white-space': 'pre-wrap'}),            
                html.Img(id='corr-plot', src='https://images.squarespace-cdn.com/content/58a4b31dbebafb6777c575b4/1549829488328-IZMTRHP7SLI9P9Z7MUSW/website_logo_head.png?content-type=image%2Fpng')
            ]),
            
            # hidden_div for storing un-needed output
            html.Div(id='placeholder', style={'display': 'none'})
        ],
        style={'display': 'flex'}
    ),
    html.Div(
        html.P(children=['The swell way of correlating wells'])
    )
    ]
)

# update curve dropdown options when new well is picked
"""update of new curve selector list when new well is triggered"""
@app.callback(
    [Output('curve-selector', 'options'),
     Output('curve-selector', 'value')],
    [Input('well-selector', 'value')])
def well_update_changes_curves(well_uwi): ##def for updating curve list and curves
    w = p.get_well(well_uwi) ## identifies and gets the correct welly.Well object based on well_uwi
    df = w.df() ## creates dataframe from welly.Well object
    curve_list = sorted(df.columns.tolist()) ##gets curve list for welly.Well object
    curve = curve_list[0] ##identifies the first curve in list for default figure
    curve_dropdown_options = [{'label': k, 'value': k} for k in curve_list] ##creates dropdown list
    return curve_dropdown_options, curve ##returns the dropdown list options and the initial curve


# update tops data when graph is clicked or new top is added
@app.callback(
    Output('tops-storage', 'children'),
    [Input('well_plot', 'clickData'),
     Input('new-top-button', 'n_clicks')],
    [State("top-selector", "value"),
     State("tops-storage", "children"),
     State('new-top-name', 'value'),
     State('well-selector', 'value'),
     State('top-selector', 'options')])
def update_pick_storage(clickData, new_top_n_clicks, active_pick, surface_picks, new_top_name, active_well, tops_options):
    """Update the json stored in tops-storage div based on y-value of click"""
    
    # Each element in the app can only be updated by one call back function.
    # So anytime we want to change the tops-storage it has to be inside of this function.
    # We need to use the dash.callback_context to determine which event triggered
    # the callback and determine which actions to take
    # https://dash.plotly.com/advanced-callbacks    
    surface_picks_df = pd.read_json(surface_picks)
    
    # get callback context
    ctx = callback_context
    if not ctx.triggered:
        event_elem_id = 'No clicks yet'
    else:
        event_elem_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # do the updating based on context
    if event_elem_id == "well_plot": # click was on the plot
        if active_pick:
            y = clickData['points'][0]['y']

            # update the tops depth df
            pick = {'UWI': active_well, 'PICK': active_pick, 'MD': y} 
            surface_picks_df = surface_picks_df.append(pick, ignore_index=True).drop_duplicates(subset=['UWI', 'PICK'], keep='last')
    
    if event_elem_id == "new-top-button": # click was on the new top button
        options = [d['value'] for d in tops_options] # tops_options is list of dicts eg [{'label': pick, 'value': pick}]
        if not new_top_name in options:
            pick = {'UWI': active_well, 'PICK': new_top_name, 'MD': np.nan} 
            surface_picks_df = surface_picks_df.append(pick, ignore_index=True).drop_duplicates(subset=['UWI', 'PICK'], keep='last')

    return surface_picks_df.to_json() 

# Update graph when tops storage changes
@app.callback(
    Output("well_plot", "figure"),
    [Input('tops-storage', 'children'),
     Input('curve-selector', 'value')],
     [State('well-selector', 'value')] ## With multiple wells the state of the well_uwi must be passed to select the right welly.Well
    )
def update_figure(surface_picks, curve, active_well):
    """redraw the plot when the data in tops-storage is updated"""  
    surface_picks = pd.read_json(surface_picks)
    surface_picks = surface_picks[surface_picks['UWI'] == active_well]

    w = p.get_well(active_well) ##selects the correct welly.Well object
    df = w.df() ##reloads the correct dataframe for the display

    # regenerate figure with the new horizontal line
    fig = px.line(x=df[curve], y=df.index, labels = {'x':curve, 'y': df.index.name})

    fig.layout = {'uirevision': curve} # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
    fig.update_yaxes(autorange="reversed")
    fig.layout.xaxis.fixedrange = True
    fig.layout.template = 'plotly_white'
    helper.update_picks_on_plot(fig, surface_picks)
    
    return fig


# update dropdown options when new pick is created
@app.callback(
    Output("top-selector", "options"),
    [Input('tops-storage', 'children')])
def update_dropdown_options(surface_picks):
    """update the options available in the dropdown when a new top is added"""
    
    surface_picks = pd.read_json(surface_picks)
    tops_dropdown_options = [{'label': k, 'value': k} for k in list(surface_picks['PICK'].unique())]
    return tops_dropdown_options


# Write tops to external file
@app.callback(
    Output('placeholder', 'children'),
    [Input('save-button', 'n_clicks')],
    [State('tops-storage', 'children'),
    State('input-save-path', 'value')])
def save_picks(n_clicks, surface_picks, path):
    """Save out picks to a json file. 
    TODO: I am sure there are better ways to handle saving out picks, but this is proof of concept"""
    #picks_df = pd.read_json(surface_picks)

    if path:
        path_to_save = Path('.') / 'well_picks' / 'data' / 'updates' / path
        with open(path_to_save, 'w') as f:
            json.dump(surface_picks, fp=f)

    return

# create striplog csv text
@app.callback(
    Output('striplog-txt', 'children'),
    [Input('gen-striplog-button', 'n_clicks'),
    Input('well-selector', 'value')],
    [State('tops-storage', 'children')])
def generate_striplog(n_clicks, active_well, surface_picks):
    print(active_well)
    surface_picks = pd.read_json(surface_picks)
    surface_picks = surface_picks[surface_picks['UWI'] == active_well]   
    s = helper.surface_pick_to_striplog(surface_picks)
    return json.dumps(s)

if __name__ == "__main__":
    app.run_server(port=4545, debug=True)