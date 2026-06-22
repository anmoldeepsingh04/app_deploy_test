# importing required packages

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from sklearn.cluster import KMeans
from scipy import ndimage
import random
import math
from IPython.display import HTML, display
import ipywidgets as widgets
from IPython.display import clear_output
import io, sys
from scipy.optimize import root_scalar
from contextlib import redirect_stdout
import os

# ==================== GLOBAL COLOR SCHEME ====================
COLORS = {
    'liquid':               (230, 255, 230),  # extremely light green (was light gray)
    'delta_ferrite':        (100, 150, 255),  # light blue
    'austenite':            (255, 100, 100),  # light red
    'alpha_ferrite':        (100, 150, 255),  # same as delta (both are ferrite)
    'proeutectoid_ferrite': (150, 200, 255),  # lighter blue for proeutectoid
    'cementite_bulk':       (255, 220, 180),  # skin colour for bulk cementite
    'cementite_boundary':   (0, 0, 0),        # black outline for large cementite
    'pearlite_ferrite':     (220, 180, 140),  # tan
    'pearlite_cementite':   (60, 60, 60),     # dark gray for pearlite cementite
    'grain_boundary':       (0, 0, 0),        # black
    'background':           (220, 220, 220),  # light gray
}
