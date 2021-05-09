import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from welly import Well,Curve


def make_log_plot(w, log_list=['GR','DT', 'TNPH', 'RHOB'], 
                  ymin=None, ymax=None, 
                  resample=None): # curve names need to be dynamic later
    '''
    create a composite log of GR and Resistivity
    TO DO:
    - need to pass the curve names and colors
    - colors should be dynamic
    - linear vs. log should be dynamic
    '''
    
    w_ymin = w.data[log_list[0]].basis[0]
    w_ymax = w.data[log_list[0]].basis[-1]
    
    if ymin is None: ymin = w_ymin
    if ymax is None: ymax = w_ymax
    if resample:         
        for log in log_list:
            try:
                w.data[log] = w.data[log].to_basis(step=resample)
            except:
                print('Resampling did not occur: ', resample, ' keeping original step.')


    #track1 = go.Scatter(x=w.data[log_list[0]].values, y=w.data[log_list[0]].basis, name=log_list[0], line=dict(color='black'))
    try:
        track1 = go.Scatter(x=w.data[log_list[0]].values, y=w.data[log_list[0]].basis, name=log_list[0], line=dict(color='black'),
                        xaxis='x1')
    except:
        track1 = go.Scatter(x=[], y=[], name="Empty", xaxis='x1')
    try:
        track2 = go.Scatter(x=w.data[log_list[1]].values, y=w.data[log_list[1]].basis, name=log_list[1], line=dict(color='red'),
                        xaxis='x2')
    except:
        track2 = go.Scatter(x=[], y=[], name="Empty", xaxis='x2')

    try:
        track3 = go.Scatter(x=w.data[log_list[2]].values, y=w.data[log_list[2]].basis, name=log_list[2], line=dict(color='red'),
                        xaxis='x3')
    except:
        track3 = go.Scatter(x=[], y=[], name="Empty", xaxis='x3')

    try:
        track4 = go.Scatter(x=w.data[log_list[3]].values, y=w.data[log_list[3]].basis, name=log_list[3], line=dict(color='black'),
                        xaxis='x4')
    except:
        track4 = go.Scatter(x=[], y=[], name="Empty", xaxis='x4')

    data = [track1, track2, track3, track4]

    figcross = go.Figure()

    figcross.add_trace(track3)
    figcross.add_trace(track4)

    figcross.update_layout(
    xaxis3=dict(
        
        
        tickfont=dict(
            color="#1f77b4"
        ),
        
    ),
    xaxis4=dict(
        
        
        tickfont=dict(
            color="#ff7f0e"
        ),
        
        overlaying="x3",
        
        #type="log", 
        #autorange='reversed',
        #range=[3,-1]
    ),
    yaxis=dict(
        domain=[0, 0.7],
        
        tickfont=dict(
            color="#1f77b4"
        )
    )
    )



    fig = make_subplots(cols=3, 
                        shared_yaxes=True,
                        horizontal_spacing=0.01,
                        subplot_titles=[log_list[0], log_list[1], log_list[2]],
                        specs=[[{}, {}, {}]],
                        figure = figcross)
    
    fig.add_traces([track1, track2],
                rows=[1,1],
                cols=[1,2]
    )
    fig.update_xaxes(row=1, col=1, range=[0,150], fixedrange=True, position=0)
    fig.update_xaxes(row=1, col=2, autorange='reversed', fixedrange=True, position=1)
    fig.update_xaxes(row=1, col=3, fixedrange=True)
    
    fig.update_yaxes(nticks=25, autorange='reversed')
    fig.update_layout(hovermode="y", template="plotly_white")



    return fig


"""
    layout = go.Layout(
        xaxis=dict(
            domain=[0, 0.3], #to keep some gap between tracks. try padding the margins instead
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
            domain=[0.3, 0.6],
            range=[140,40],
            type='linear', # change to variable later
            position=1,
            title=log_list[1] 
            ),
        xaxis3=dict(
            domain=[0.6, 1],
            range=[0,3],
            type='log', # change to variable later
            position=1,
            title=log_list[2] 
            ),
        xaxis4=dict(
            domain=[0.6, 1],
            range=[0,2],
            type='log', # change to variable later
            position=0.85,
            title=log_list[3],
            
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
"""
    


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