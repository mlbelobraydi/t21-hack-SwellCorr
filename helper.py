import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from welly import Well,Curve


def make_log_plot(w, log_list=['GR','DT'], 
                  ymin=None, ymax=None, 
                  resample=None): # curve names need to be dynamic later
    '''
    create a composite log of GR and Resistivity
    TO DO:
    - need to pass the curve names and colors
    - colors should be dynamic
    - linear vs. log should be dynamic
    '''
    #resample @ None # resample curves to higher resolution
    
    w_ymin = w.data[log_list[0]].basis[0]
    w_ymax = w.data[log_list[0]].basis[-1]

    
    if ymin is None: ymin = w_ymin
    if ymax is None: ymax = w_ymax
    
    resample_step = 0.05 #static value for reasonable 
    for log in log_list:
        w.data[log] = w.data[log].to_basis(step=resample_step)

    track1 = go.Scatter(x=w.data[log_list[0]].values, y=w.data[log_list[0]].basis, name=log_list[0], line=dict(color='black'))
    track2 = go.Scatter(x=w.data[log_list[1]].values, y=w.data[log_list[1]].basis, name=log_list[1], line=dict(color='red'),
                        xaxis='x2')

    data = [track1, track2]

    layout = go.Layout(
        xaxis=dict(
            domain=[0, 0.45], #to keep some gap between tracks. try padding the margins instead
            range=[0,150], # need to be range values later
            #type='linear', # change to variable later
            position=1,
            title=log_list[0], #this is the axis title, need to figure out how to turn on the subplot title
            titlefont=dict(
            color="black"), # change to variable later
            tickfont=dict(
            color="black") #change to variable later
            ),
        xaxis2=dict(
            domain=[0.55, 1],
            range=[140,40],
            type='linear', # change to variable later
            position=1,
            title=log_list[1] 
            ),
        yaxis=dict(
            domain=[0,0.95] #controlling the top of the plot so the name and scale are visible
            ),
        hovermode="y",
        template='plotly_white',
        
        )
    fig = go.Figure(data=data, layout=layout, layout_title_text=w.name)
    fig.update_yaxes(range=(ymax,ymin)) # reversed for MD assumption
    fig.layout.xaxis.fixedrange = True
    fig.layout.xaxis2.fixedrange = True #added this line also to control zoom on the second track
   

    return fig


def update_picks_on_plot(fig, surface_picks):
    """Draw horizontal lines on a figure at the depths of the values in the
       surface picks dictionary"""

    fig.update_layout(
        shapes=[
            dict(
                type="line",
                yref="y",
                y0=md,
                y1=md,
                xref="paper",
                x0=0 ,  
                x1=1,   # https://github.com/plotly/plotly_express/issues/143#issuecomment-535494243
            ) 
            for md in surface_picks["MD"] if not np.isnan(md)
        ], # list comprehension iterating over the surface picks dictionary

        annotations=[
            dict(
                x=.5,
                y=md,
                xref="paper",
                yref="y",
                text=top_name,
                ax=0,
                ay=-8
            )
            for md, top_name in zip(surface_picks['MD'], surface_picks['PICK']) if not np.isnan(md)
        ]
    )
    return


def surface_pick_to_striplog(surface_picks):
    """
    Generate a striplog csv
    """
    s = surface_picks[['PICK', 'MD']]
    s.columns = ['Comp Formation', 'Depth']
    csv_text = s.to_csv()
    return csv_text