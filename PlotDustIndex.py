import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta
import os
from netCDF4 import Dataset
import pandas as pd

from bokeh.models import ColumnDataSource, Range1d, HoverTool, Button, CustomJS
from bokeh.io import show,curdoc
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.embed import components



def randomData():
    """
    creates a random dataframe for debuging issues
    :return: pandas dataframe
    """
    data1 = np.asarray(np.abs(np.random.normal(0.5,0.5,719)))
    data2 = np.asarray(np.abs(np.random.normal(0.5,0.5,719)))
    start_time = dt(2017,1,1,0,0,0)
    time = []
    for i in range(len(data)):
        time.append(start_time + timedelta(seconds=120*(i+1)))
    time = np.asarray(time)

    df = pd.DataFrame({'time':time,'DIL':data1,'DIT':data2})
    df = df[::-1]

    return df

def saveGrid(grid):
    script, div = components(grid)
    script = script[35:]  # removes the <script> tag at the beginning
    script = script[:-9]  # removes the </script> tag at the end

    # Replace the elementid in the script:
    start_index = script.index("elementid") + 12

    end_index = start_index
    for c in script[start_index:]:
        if (c == ','):
            break
        else:
            end_index += 1
    end_index -= 1
    replace_me = script[start_index:end_index]
    script = script.replace(replace_me, 'AvailabilityPlotElementID')
    print(replace_me)

    # write everything out as .js file:
    with open("DustIndexPlot.js", "w") as f:
        f.write("/*This code is generated by a python Script.")
        f.write("\nScript name: " + os.path.basename(__file__))
        f.write("\nLast modification: " + dt.today().strftime("%x"))
        f.write("\nAuthor: Tobias Machnitzki (tobias.machnitzki@mpimet.mpg.de) */\n")
        f.write(script)
        f.close()

def Initialize(datestr):
    # Parameter:
    NC_PATH = "/pool/OBS/ACPC/RamanLidar-LICHT/3_QuickLook/nc/ql{}/".format(datestr[2:6])
    NC_NAME = "/li{}.b532".format(datestr[2:])

    # Get data from nc-file:
    nc = Dataset(NC_PATH + NC_NAME)
    dustIndexLow = nc.variables["DustIndexLowLayer"][:].copy()
    dustIndexTotal = nc.variables["DustIndexTotal"][:].copy()
    seconds = nc.variables["Time"][:].copy()
    nc.close()

    # Handle missing Values:
    dustIndexTotal[np.where(dustIndexTotal > 1e30)] = np.nan
    dustIndexLow[np.where(dustIndexLow > 1e30)] = np.nan

    # Shape time to the right format:
    time = []
    start_time = dt(int(datestr[:4]), int(datestr[4:6]), int(datestr[6:]), 0, 0, 0)
    for t in seconds:
        time.append(start_time + timedelta(seconds=int(t)))
    time = np.asarray(time)
    df = pd.DataFrame({'time': time, 'DIL': dustIndexLow, 'DIT': dustIndexTotal})
    df = df[::-1] # reverse columns
    return df

def createHoverTool():
    hover = HoverTool(
        names=["DIL-Line"],
        tooltips=[
            ('time', '@time{%F}'),
            ('DIL', '@{DIL}{%0.8f}'),
            ('DIT', '@{DIT}{%0.8f}'),
        ],
        formatters={
            'time': 'datetime',  # use 'datetime' formatter for 'date' field
            'DIL': 'printf',  # use 'printf' formatter
            'DIT': 'printf',  # use 'printf' formatter
        },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='vline'
    )
    return hover

def setGrid(both=False):
    if both:
        grid = gridplot([[p1], [p2]], plot_width=1200, plot_height=300)
    else:
        grid = gridplot([[p1]], plot_width=1200, plot_height=300)
    return grid

def update():
    source.data = source.from_df(data[['time','DIL','DIT']])
    source_static.data = source.data

if __name__ == "__main__":
    datestr = "20171111"
    data = Initialize(datestr)


    source = ColumnDataSource(data=dict(time=[],DIL=[],DIT=[]))
    source_static = ColumnDataSource(data=dict(time=[],DIL=[],DIT=[]))


    # time,data = randomData()

    factors = ["Dust Index Low", "Dust Index Total"]
    means = [data['DIL'].mean(0), data['DIT'].mean(0)]

    levels ={0    :"Very Low",
             0.01 : "Low",
             0.02 : "Middle",
             0.03 : "High",
             0.5  : "Very High"}

    #TODO: Write the level on top of the Line

    hover = createHoverTool()
    button = Button(name="show_more",label="More information", button_type="success",width=150,height=0,
                    callback=(CustomJS(code=open("show_more_callback.js").read())))

    toolbox = [hover]
    x_range = Range1d(start=0, end=0.01)
    p1 = figure(title="Dust Index", responsive=True,x_range=x_range,y_range=factors, tools="")
    p1.segment(0, factors, means , factors, line_width=4, line_color="black", )
    p1.circle(means, factors, size=15, fill_color="orange", line_color="black", line_width=3, )
    p1.xaxis.visible = False
    p1.xgrid.visible = False
    p1.ygrid.visible = False
    p1.border_fill_color = None
    p1.background_fill_color = None

    p2 = figure(responsive=True, tools=toolbox)
    p2.line(x="time",y="DIL",source=source,line_width=3,line_color='blue',name='DIL-Line')
    p2.line(x="time",y="DIT",source=source,line_width=3,line_color='red')
    p2.border_fill_color = None
    p2.background_fill_color = None

    grid = gridplot([[p1],[p2]], plot_width=1200,plot_height=300)
    grid = gridplot([[p1]], plot_width=1200, plot_height=300)
    # initialize bottom graph:
    update()
    grid = setGrid()

    curdoc().add_root(grid)

    # show(grid)
    saveGrid(grid)