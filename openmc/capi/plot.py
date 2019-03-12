from ctypes import c_int, c_int32, c_double, Structure, POINTER

from . import _dll
from .core import _DLLGlobal
from .error import _error_handler

import numpy as np


class _Position(Structure):
    """Definition of an xyz location in space with underlying c-types

    C-type Attributes
    -----------------
    x : c_double
        Position's x value (default: 0.0)
    y : c_double
        Position's y value (default: 0.0)
    z : c_double
        Position's z value (default: 0.0)
    """
    _fields_ = [('x', c_double),
                ('y', c_double),
                ('z', c_double)]

    def __repr__(self):
        return "({}, {}, {})".format(self.x, self.y, self.z)

    def __str__(self):
        return self.__repr__()

class _PlotBase(Structure):
    """A structure defining a 2-D geometry slice with underlying c-types

    C-Type Attributes
    -----------------
    origin : openmc.capi.plot._Position
        A position defining the origin of the plot.
    width_ : openmc.capi.plot._Position
        The width of the plot along the x, y, and z axes, respectively
    basis_ : c_int
        The axes basis of the plot view.
    pixels_ : c_int[3]
        The resolution of the plot in the horizontal and vertical dimensions
    level_ : c_int
        The universe level for the plot view

    Attributes
    ----------
    origin : tuple or list of ndarray
        Origin (center) of the plot
    width : float
        The horizontal dimension of the plot in geometry units (cm)
    height : float
        The vertical dimension of the plot in geometry units (cm)
    basis : string
        One of {'xy', 'xz', 'yz'} indicating the horizontal and vertical
        axes of the plot.
    h_res : float
        The horizontal resolution of the plot in pixels
    v_res : float
        The vertical resolution of the plot in pixels
    level : int
        The universe level for the plot (default: -1 -> all universes shown)
    """
    _fields_ = [('origin_', _Position),
                ('width_', _Position),
                ('basis_', c_int),
                ('pixels_', 3*c_int),
                ('level_', c_int)]

    def __init__(self):
        self.level_ = -1

    @property
    def origin(self):
        out = [self.origin_.x, self.origin_.y, self.origin_.z]
        return [float(val) for val in out]

    @property
    def width(self):
        return float(self.width_.x)

    @property
    def height(self):
        return float(self.width_.y)

    @property
    def basis(self):
        if self.basis_ == 1:
            return 'xy'
        elif self.basis_ == 2:
            return 'xz'
        elif self.basis_ == 3:
            return 'yz'

        raise ValueError("Plot basis {} is invalid".format(basis_))

    @property
    def h_res(self):
        return self.pixels_[0]

    @property
    def v_res(self):
        return self.pixels_[1]

    @property
    def level(self):
        return int(self.level_)

    @origin.setter
    def origin(self, origin):
        self.origin_.x = origin[0]
        self.origin_.y = origin[1]
        self.origin_.z = origin[2]

    @width.setter
    def width(self, width):
        self.width_.x = width

    @height.setter
    def height(self, height):
        self.width_.y = height

    @basis.setter
    def basis(self, basis):
        if isinstance(basis, str):
            valid_bases = ('xy', 'xz', 'yz')
            basis = basis.lower()
            if basis not in valid_bases:
                raise ValueError("{} is not a valid plot basis.".format(basis))

            if basis == 'xy':
                self.basis_ = 1
            elif basis == 'xz':
                self.basis_ = 2
            elif basis == 'yz':
                self.basis_ = 3
            return

        if isinstance(basis, int):
            valid_bases = (1, 2, 3)
            if basis not in valid_bases:
                raise ValueError("{} is not a valid plot basis.".format(basis))
            self.basis_ = basis
            return

        raise ValueError("{} of type {} is an"
                         " invalid plot basis".format(basis, type(basis)))

    @h_res.setter
    def h_res(self, h_res):
        self.pixels_[0] = h_res

    @v_res.setter
    def v_res(self, v_res):
        self.pixels_[1] = v_res

    @level.setter
    def level(self, level):
        self.level_ = level

    def __repr__(self):
        out_str = ["-----",
                   "Plot:",
                   "-----",
                   "Origin: {}".format(self.origin),
                   "Width: {}".format(self.width),
                   "Height: {}".format(self.height),
                   "Basis: {}".format(self.basis),
                   "HRes: {}".format(self.h_res),
                   "VRes: {}".format(self.v_res),
                   "Level: {}".format(self.level)]
        return '\n'.join(output)

    def __str__(self):
        return self.__repr__()


_dll.openmc_id_map.argtypes = [POINTER(_PlotBase), POINTER(c_int32)]
_dll.openmc_id_map.restype = c_int
_dll.openmc_id_map.errcheck = _error_handler


def id_map(plot):
    """
    Generate a 2-D map of (cell_id, material_id). Used for in-memory image
    generation.

    Parameters
    ----------
    plot : An openmc.capi.plot._PlotBase
        Object describing the slice of the model to be generated

    Returns
    -------
    id_map : numpy.ndarray
        A NumPy array with shape (vertical pixels, horizontal pixels, 2) of
        OpenMC property ids with dtype int32

    """
    img_data = np.zeros((plot.v_res, plot.h_res, 2),
                        dtype=np.dtype('int32'))
    _dll.openmc_id_map(POINTER(_PlotBase)(plot),
                       img_data.ctypes.data_as(POINTER(c_int32)))
    return img_data
