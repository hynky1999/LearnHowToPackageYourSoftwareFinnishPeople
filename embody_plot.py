#!/usr/bin/env python

"""
Visualize emBODY data

This python script is based on matlab code found from:
https://version.aalto.fi/gitlab/eglerean/embody/tree/master/matlab

Data is loaded from hardcoded experiment (exp_id)
-> TODO: create argument parser where user determines which 
         experiment is used or if data is loaded from all answers

Requirements:
    - python 3+
    - matplotlib
    - numpy
    - scipy

Run:
python embody_plot.py
"""

import sys
import time
import datetime
import json
import resource
import mysql.connector as mariadb
import io
import urllib, base64
import argparse

import numpy as np
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

# Hard coded image size
WIDTH = 207
HEIGHT = 600

# image paths
IMAGE_PATH = './app/static/img/dummy_600.png'
IMAGE_PATH_MASK = './app/static/img/dummy_600_mask.png'
STATIC_PATH = './app/static/'

# Interpolation methods
METHODS = ['none','bilinear', 'bicubic', 'gaussian']

# SELECT methods
SELECT_ALL = ("SELECT coordinates from embody_answer")
SELECT_BY_EXP_ID = 'select coordinates from embody_answer as em JOIN (SELECT idanswer_set FROM answer_set as a JOIN experiment as e ON a.experiment_idexperiment=e.idexperiment AND e.idexperiment=%s) as ida ON em.answer_set_idanswer_set=ida.idanswer_set'
SELECT_BY_ANSWER_SET = 'select coordinates from embody_answer WHERE answer_set_idanswer_set=%s'
SELECT_BY_PAGE = 'select coordinates from embody_answer WHERE page_idpage=%s'

'''
mariadb_connection = mariadb.connect(
    user='rating', 
    password='rating_passwd', 
    database='rating_db'
)
'''
    
# Get date
now = datetime.datetime.now()
DATE_STRING = now.strftime("%Y-%m-%d")


class MyDB(object):

    def __init__(self):
        self._db_connection = mariadb.connect(user='rating', password='rating_passwd', database='rating_db')
        self._db_cur = self._db_connection.cursor()

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()



def matlab_style_gauss2D(shape=(1,1),sigma=5):
    """2D gaussian mask - should give the same result as MATLAB's
    fspecial('gaussian',[shape],[sigma])"""

    m,n = [(ss-1.)/2. for ss in shape]
    y,x = np.ogrid[-m:m+1,-n:n+1]
    h = np.exp( -(x*x + y*y) / (2.*sigma*sigma) )
    h[ h < np.finfo(h.dtype).eps*h.max() ] = 0
    sumh = h.sum()
    if sumh != 0:
        h /= sumh
    return h


def map_coordinates(a,b,c=None):
    return [a,b,c]


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result

    return timed


@timeit
def get_coordinates(selected_value, select_clause=SELECT_BY_PAGE):
    """Select all drawn points from certain stimulus and plot them onto 
    the human body"""

    db = MyDB()
    db.query(select_clause, (selected_value,))

    # Get coordinates
    coordinates = format_coordinates(db._db_cur)

    # Draw image
    plt = plot_coordinates(coordinates)

    # Save image to ./app/static/ 
    img_filename = 'PAGE-' + str(selected_value) + '-' + DATE_STRING + '.png'
    plt.savefig(STATIC_PATH + img_filename)

    # Return image path to function caller
    return img_filename


def format_coordinates(cursor):
    # Init coordinate arrays and radius of point
    x=[]
    y=[]
    r=[]
    standard_radius=13

    # Loop through all of the saved coordinates and push them to coordinates arrays
    for coordinate in cursor:
        try:
            coordinates = json.loads(coordinate[0])
            x.extend(coordinates['x'])
            y.extend(coordinates['y'])
            r.extend(coordinates['r'])
        except KeyError:
            standard_radiuses = np.full((1, len(coordinates['x'])), standard_radius).tolist()[0]
            r.extend(standard_radiuses)
            continue

    return {
        "x":x,
        "y":y,
        "coordinates":list(map(map_coordinates, x,y,r))
    }

from flask_socketio import emit
from app import socketio

def plot_coordinates(coordinates):

    # Total amount of points
    points_count = len(coordinates['coordinates']) 

    # Load image to a plot
    image = mpimg.imread(IMAGE_PATH)
    image_mask = mpimg.imread(IMAGE_PATH_MASK)

    # Init plots
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)

    # Plot coordinates as points
    ax1.set_title("raw points")
    ax1.plot(coordinates["x"],coordinates["y"], 'ro', alpha=0.2)
    ax1.imshow(image)

    # Draw circles from coordinates (imshow don't need interpolation)
    # TODO: set sigma according to brush size!
    ax2.set_title("gaussian disk around points")
    frame = np.zeros((HEIGHT,WIDTH))

    for idx, point in enumerate(coordinates["coordinates"]):
        frame[point[1], point[0]] = 1
        point = ndimage.gaussian_filter(frame, sigma=5)
        ax2.imshow(point, cmap='hot', interpolation='none')

        # Try to send progress information to socket.io
        try:
            socketio.sleep(0)
            emit('progress', {'done':idx+1/points_count, 'from':points_count})
        except RuntimeError as err:
            continue

    ax2.imshow(image_mask)

    # Draw a gaussian heatmap on the whole image
    # NOT USABLE
    '''
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)
    extent=[x_min, x_max, y_min, y_max]
    extent_all = [0,WIDTH,0,HEIGHT]
    plt.subplot2grid((2, 2), (1, 1))
    plt.title('gaussian heatmap')
    plt.imshow(image)
    plt.imshow(coordinates, extent=extent_all, cmap='hot', interpolation='gaussian')
    plt.imshow(image_mask)
    '''

    # return figure for saving/etc...
    return fig

    '''
    # Return image as bytes 
    fig = plt.gcf()
    imgdata = io.BytesIO()
    fig.savefig(imgdata, format='png')
    imgdata.seek(0)  # rewind the data
    return imgdata.read()

    #Show image
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plt.show()
    '''


if __name__=='__main__':
    
    arg_parser = argparse.ArgumentParser(description='Draw bodily maps of emotions')
    arg_parser.add_argument('-s','--stimulus', help='Select drawn points from certain stimulus', required=False, action='store_true')
    arg_parser.add_argument('-e','--experiment', help='Select drawn points from certain experiment', required=False, action='store_true')
    arg_parser.add_argument('-a','--answer-set', help='Select drawn points from certain answer_set', required=False, action='store_true')
    arg_parser.add_argument('integers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')
    args = vars(arg_parser.parse_args())
    value = args['integers'][0]

    if args['stimulus']:
        get_coordinates(value, SELECT_BY_PAGE)
    elif args['experiment']:
        get_coordinates(value, SELECT_BY_EXP_ID)
    elif args['answer_set']:
        get_coordinates(value, SELECT_BY_ANSWER_SET)
    else:
        print("No arguments given. Exit.")
        sys.exit(0)



