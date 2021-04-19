import numpy as np

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