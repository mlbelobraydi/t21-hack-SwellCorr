import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objs as go

def make_log_plot(df, log_list=['GR','RD']):
    '''
    create a composite log of GR and Resistivity
    '''
    gammaray = go.Scatter(x=df['GR'].values.tolist(), y=df.index, name='Gamma Ray', line=dict(color='limegreen'))
    resistivity = go.Scatter(x=df['RD'].values.tolist(), y=df.index, xaxis='x2', name='Resistivity')

    data = [gammaray, resistivity]

    layout = go.Layout(
        xaxis=dict(
            domain=[0, 0.45], 
            range=[0,120],
            position=1,
            title="GR",
            titlefont=dict(
            color="limegreen"
        ),
        tickfont=dict(
            color="limegreen")
                        
        ),
        xaxis2=dict(
            domain=[0.55, 1],
            range=[-1,4],
            type='log',
            position=1,
            title="Res"
        ),
        hovermode="y",
        template='plotly_white'
        )
    fig = go.Figure(data=data, layout=layout)
    fig.update_yaxes(autorange="reversed") #can i put this in with the layout
    return fig

def update_picks_on_plot(fig, surface_picks):
    """Draw horizontal lines on a figure at the depths of the values in the
       surface picks dictionary"""

    print(surface_picks)

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