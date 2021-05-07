from welly import Well, Project # Welly is used to organize the well data and project collection
from striplog import Legend, Striplog
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import ticker
from dash import Dash, callback_context # dash is used to update the plot and fields dynamically in a web browser
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import flask
from glob import glob
import json
import numpy as np
import pandas as pd
from pathlib import Path
import base64
import os
import helper
import xsection as xs

matplotlib.use('Agg')


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Create server variable with Flask server object for use with gunicorn
server = app.server

# Get las files
path = 'data/Poseidon_data/las/' # direct link to specific data
lasfiles = glob(path + '*.LAS')

# Get striplog files
path2 = 'data/Poseidon_data/tops/' # direct link to specific data
stripfiles = glob(path2 + '*.csv')

legend = Legend.from_csv(filename='data/Poseidon_data/tops_legend.csv') # direct link to specific data

p = Project.from_las('data/Poseidon_data/las/*.LAS') # direct link to specific data
well_uwi = [w.uwi for w in p] ##gets the well uwi data for use in the well-selector tool

# Add striplogs to Project
# Striplog must have the same name as LAS file.
# e.g. Torosa-1.LAS and Torosa-1.csv
for w in p:
    name = Path(w.fname).stem
    strip = Striplog.from_csv(f'data/Poseidon_data/tops/{name}.csv')  # direct link to specific data
    w.data['tops'] = strip


well = p[0]  ##gets data from the first well in the Welly Project
curve_list = xs.get_curves(p) ##gets the column names for later use in the curve-selector tool
curve = xs.get_first_curve(curve_list)
surface_picks_df = xs.get_tops_df(p)

#well dropdown selector
well_dropdown_options = [{'label': k, 'value': k} for k in sorted(well_uwi)] ##list of wells to the dropdown
#tops dropdown options
"""we need to have a stratigraphic column at some point"""
tops_dropdown_options = [{'label': k, 'value': k} for k in list(surface_picks_df['PICK'].unique())] ##list of tops to the dropdown
##well log curve dropdown options
curve_dropdown_options = [{'label': k, 'value': k} for k in sorted(curve_list)] ##list of well log curves to the dropdown

# draw the initial plot
#plotting only GR and RD in a subplot
ymin, ymax = 3000, 5500 # make dynamic later
fig_well_1 = helper.make_log_plot(w=well, ymin=ymin)

app.title = "SwellCorr"

controls = dbc.Card(
        children=[
       
            dbc.FormGroup(
                [
                    dbc.Label("Select Well"),
                    dcc.Dropdown(id='well-selector', 
                                options=well_dropdown_options,
                                value=p[0].uwi,
                    ),
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label("Select a Pick to Edit"),
                    dcc.Dropdown(id='top-selector', 
                                 options=tops_dropdown_options, 
                                 placeholder="Select a top to edit")
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Create a New Pick'),
                    dbc.Input(id='new-top-name', placeholder='Name for new top', type='text', value=''),
                    html.Button('Create', id='new-top-button', className='btn-primary')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Select A Curve'),
                    dcc.Dropdown(id='curve-selector', options=curve_dropdown_options, value='', placeholder="Select a curve"),

                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label("Write tops to file"),
                    dbc.Input(id='input-save-path', type='text', placeholder='path_to_save_picks.json', value=''),
                    html.Button('Save Tops', id='save-button', n_clicks=0, className='btn-primary')
                ]
            ),
            dbc.FormGroup(
                [
                    html.Button('Update Striplog', id='gen-striplog-button', className='btn-primary')
                ]
            )
        ],
        body=True
        )


         
app.layout = dbc.Container(
                children=[
                    html.H1('🌊 SwellCorr well correlation 🌊'),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(controls, width=2),
                            dbc.Col(dcc.Graph(id="well_plot", 
                                              figure=fig_well_1,
                            style={'height': 1200}),
                                    width=3),
                            dbc.Col([
                                dash_table.DataTable(
                                        id='table',
                                        columns=[
                                            {"name": i, "id": i, "deletable": False, "selectable": False, "hideable": False}
                                            for i in surface_picks_df.columns
                                        ],
                                        data=surface_picks_df.to_dict('records'),
                                        editable=True,
                                        sort_action='native',
                                        sort_mode='multi',
                                        filter_action='native',
                                        style_table={'overflowY': 'scroll', 'height': '300px', 'width': '90%'},
                                        style_cell={'width': '{}%'.format(len(surface_picks_df.columns))},
                                        ),

                                    # hidden_div for storing tops data as json
                                    html.Div(id='tops-storage', children=surface_picks_df.to_json(), 
                                        style={'display': 'none'}
                                        ),

                                    html.Hr(),
                                    # html.H4('Striplog CSV Text:'),
                                    # html.Pre(id='striplog-txt', children='', style={'white-space': 'pre-wrap'}),            
                                    html.Img(id='cross-section', src=xs.encode_xsection(p, legend),
                                             style={'display': 'block',
                                                    'margin-left': 'auto',
                                                    'margin-right': 'auto',
                                                    }),
                                    html.Div(id='placeholder', style={'display': 'none'}),
                                ], width=7)
                        ]),
                    html.Hr(),
                    html.A(
                           [html.Img(id='logo', src='https://images.squarespace-cdn.com/content/v1/58a4b31dbebafb6777c575b4/1552228857222-IT0RG669ZUOLLLR597EU/ke17ZwdGBToddI8pDm48kLPswmMOqQZ9-Q6KHLjvbpZ7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QPOohDIaIeljMHgDF5CVlOqpeNLcJ80NK65_fV7S1UcaEU9usEQgaPMYSSHCLDdjcUDfwtSR5qjoqJbWx-aCIZDqXZYzu2fuaodM4POSZ4w/swung_round_no_text.png?format=500w',
                                  style={'padding-left' : 100, 'height' : '10%', 'width' : '10%'})],
                            href='https://softwareunderground.org/',
                            target='_blank'),
                    html.P(children=['The swell way of correlating wells 🌊'])
                    ], 
                fluid=True
            )
#write a callback to update the data table from the json in hidden div
@app.callback(
    Output('table', 'data'),
    [Input('tops-storage', 'children')]
    )
def update_data_table(surface_picks):
    '''
    TO DO
    need to find a way to take edits from the data table and write back to json
    so that this can also be a way to edit the tops
    '''
    surface_picks = pd.read_json(surface_picks).sort_values(['UWI','MD'], ascending = (True, True))
    return surface_picks.to_dict('records')

@app.callback(
    Output('cross-section', 'src'),
    [Input('tops-storage', 'children')],
    [State('well-selector', 'value')])
def update_cross_section(tops_storage, well_uwi):
    """
    top_storage_json to striplogs to project. 
    to return encoded str (image)
    """
    wells_tops = pd.read_json(tops_storage)
    well_tops = wells_tops[wells_tops.UWI == well_uwi]
    csv_txt = xs.df_to_csvtxt(well_tops)
    p.get_well(well_uwi).data['tops'] = Striplog.from_csv(text=csv_txt)
    return xs.encode_xsection(p, legend)


@app.callback(
    [Output('curve-selector', 'options'),
     Output('curve-selector', 'value')],
    [Input('well-selector', 'value')])
def well_update_changes_curves(well_uwi):  
    """
    def for updating curve list and curves
    """
    w = p.get_well(well_uwi)  # identifies and gets the correct welly.Well object based on well_uwi
    curve_list = sorted(list(w.data))
    curve = xs.get_first_curve(curve_list)
    curve_dropdown_options = [{'label': k, 'value': k} for k in curve_list]  #creates dropdown list
    return curve_dropdown_options, curve  # returns the dropdown list options and the initial curve


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
def update_figure(picks, curve, active_well):
    """redraw the plot when the data in tops-storage is updated"""  
    w = p.get_well(active_well) ##selects the correct welly.Well object
    picks_df = pd.read_json(picks)
    picks_selected = picks_df[picks_df['UWI'] == active_well.replace(' ', '-')]
    
    # regenerate figure with the new horizontal line
    fig = helper.make_log_plot(w=w, ymin=ymin)# , resample=0.1) # resample needs a float to change basis
    fig.update_layout(uirevision=active_well)
    helper.update_picks_on_plot(fig, picks_selected)
    
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
    """
    Save out picks to a json file. 
    TODO: I am sure there are better ways to handle saving out picks, but this is proof of concept
    """
    #picks_df = pd.read_json(surface_picks)

    if path:
        path_to_save = Path('.') / 'data' / 'updates' / path
        with open(path_to_save, 'w') as f:
            json.dump(surface_picks, fp=f)

    return

# # create striplog csv text
# @app.callback(
#     Output('striplog-txt', 'children'),
#     [Input('gen-striplog-button', 'n_clicks'),
#     Input('well-selector', 'value')],
#     [State('tops-storage', 'children')])
# def generate_striplog(n_clicks, active_well, surface_picks):
#     surface_picks = pd.read_json(surface_picks)
#     surface_picks = surface_picks[surface_picks['UWI'] == active_well]   
#     s = helper.surface_pick_to_striplog(surface_picks)
#     return json.dumps(s)

if __name__ == "__main__":
    app.run_server(port=4545, debug=True)