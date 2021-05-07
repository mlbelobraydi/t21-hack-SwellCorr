import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
import pandas as pd
from welly import Well, Project # Welly is used to organize the well data and project collection
from striplog import Legend, Striplog
import base64

def get_curves(p):
    """
    Gets a list of curves from the wells in the project
    """
    curve_list = []
    for well in p:
        curves = well.data.keys()
        for c in curves:
            curve_list.append(c)
    return sorted(set(curve_list))


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


def make_well_project(laspath='data/las/', stripath='data/tops/'):
    """
    Return a dictionary of wells and striplogs where the
    key is the base filename

    This assumes that the las file and tops files have the same name
    """
    wells = {}
    lasfiles = glob(laspath + '*.LAS')
    stripfiles = glob(stripath + '*.csv')
    for fname, sname in zip(lasfiles, stripfiles):
        name = Path(fname).stem
        wells[name] = Well.from_las(fname)
        wells[name].data['tops'] = Striplog.from_csv(sname)
        proj = Project(list(wells.values()))
    return proj


def section_plot(p, legend, ymin=3000, ymax=5500, sorted_well_list=None):
    
    if sorted_well_list:
        print('SORTED WELL LIST:', sorted_well_list)
        print('LENGTH OF P before sorting', len(p))
        p = sort_project(p, sorted_well_list)
        for w in p:
            print(w.uwi)
        print('LENGTH or SORTED PROJ', len(p))

    print("NUMBER OF AXES: ", len(p))
    if len(p) == 1:
        fig, ax = plt.subplots(ncols=1, figsize=(len(p)*2.5, 12))
        ax =  plot_well(ax, p[0], legend=legend, depth_ticks=False)
    else:
        fig, axs  = plt.subplots(ncols=len(p), figsize=(len(p)*1.0, 10))
        for i, w in enumerate(p):
            print(i, w.uwi)
            if i == 0:
                axs[i] = plot_well(axs[i], w, legend=legend, depth_ticks=True)
            else:
                axs[i] = plot_well(axs[i], w, legend=legend)
    plt.tight_layout()
    return fig


def setup_ax(ax, ymin, ymax, depth=False, major=100, minor=25):
    """Set up common parameters for the Axes in the example."""
    # only show the bottom spine
    ax.yaxis.set_major_locator(ticker.NullLocator())
    ax.spines.right.set_color('none')
    ax.spines.left.set_color('grey')
    ax.spines.top.set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.tick_params(which='major', width=1.00, length=5)
    ax.tick_params(which='minor', width=0.75, length=2.5)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(major))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(minor))
    ax.patch.set_alpha(0.0)
    ax.tick_params(axis='y', labelsize=5)
    ax.set_ylim(ymax, ymin)
    return 


def plot_well(ax, w, legend, depth_ticks=False, ymin=3000, ymax=5500):
    ax.set_title(w.header.uwi, fontsize=7, loc='center', fontweight='bold', 
                rotation=rot_title(w.header.uwi))
    plot_tops(ax, w.data['tops'], field='formation', ymin=ymin, ymax=ymax)
    w.data['tops'].plot(ax=ax, legend=legend, alpha=0.5)
    ax.plot(w.data['GR'] / 120, w.data['GR'].basis, c='k', lw=0.5)
    ax.set_xlim(0, 175 / 120)
    if depth_ticks == False:
        ax.set_yticklabels([])
    setup_ax(ax, ymin=ymin, ymax=ymax)
    return ax


def get_first_curve(curve_list):
    if 'GR' in curve_list:
        curve = 'GR'
    else:
        curve = curve_list[0] ## gets the first curve name for the plotly figure
    return curve


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
            ax.axhline(y, color='dimgrey', lw=2, zorder=0)
            ax.text(0.1, y, t, 
                    fontsize=5, color=(0.2,0.2,0.2,1), ha='left', va='center', 
                    bbox=dict(facecolor='white',
                              edgecolor='None', #edgecolor='lightgrey',
                              boxstyle='round, pad=0.1',
                              alpha=0.85))
    return


def rot_title(title, max_title_len=10):
    if len(title) > max_title_len:
        rotate = 90
    else:
        rotate = 0
    return rotate


def encode_xsection(p, legend, savefig=True):
    """
    Takes the project and saves a xsec PNG a disk and encodes it for dash
    """
    fig = section_plot(p, legend)
    image_filename = 'cross_section.png' # replace with your own image 
    if savefig:
        fig.savefig(image_filename)
    encoded_image = base64.b64encode(open(image_filename, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())