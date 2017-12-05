''' optional tools for colorimetry, wrapping the color-science library, see:
    http://colour-science.org/
'''
import numpy as np

try:
    import colour
except ImportError:
    # Spectrum objects can be used without colour
    pass

from prysm.util import share_fig_ax
from prysm.geometry import generate_mask
from prysm.mathops import nan

# some CIE constants
CIE_K = 24389 / 27
CIE_E = 216 / 24389

class Spectrum(object):
    ''' Representation of a spectrum of light.
    '''
    def __init__(self, wavelengths, values):
        ''' makes a new Spectrum instance.

        Args:
            wavelengths (`numpy.ndarray`): wavelengths values correspond to.
                units of nanometers.

            values (`numpy.ndarray`): values associated with the wavelengths.
                arbitrary units.

        Returns:
            `Spectrum`: new Spectrum object.

        '''
        self.wavelengths = np.asarray(wavelengths)
        self.values = np.asarray(values)
        self.meta = dict()

    def plot(self, xrange=None, yrange=(0, 100), fig=None, ax=None):
        ''' Plots the spectrum.

        Args:
            xrange (`iterable`): pair of lower and upper x bounds.

            yrange (`iterable`): pair of lower and upper y bounds.

            fig (`matplotlib.figure.Figure`): figure to plot in.

            ax (`matplotlib.axes.Axis`): axis to plot in.

        Returns:
            `tuple` containing:

                `matplotlib.figure.Figure`: figure containign the plot.

                `matplotlib.axes.Axis`: axis containing the plot.

        '''

        fig, ax = share_fig_ax(fig, ax)

        ax.plot(self.wavelengths, self.values)
        ax.set(xlim=xrange, xlabel=r'Wavelength $\lambda$ [nm]',
               ylim=yrange, ylabel='Transmission [%]')

        return fig, ax

class CIEXYZ(object):
    ''' CIE XYZ 1931 color coordinate system.
    '''

    def __init__(self, x, y, z):
        ''' Creates a new CIEXYZ object.

        Args:
            x (`numpy.ndarray`): array of x coordinates.

            y (`numpy.ndarray`): array of y coordinates.

            z (`numpy.ndarray`): z unit array.

        Returns:
            `CIEXYZ`: new CIEXYZ object.

        '''
        self.x = x
        self.y = y
        self.z = z

    def to_xy(self):
        ''' Returns the x, y coordinates
        '''
        check_colour()
        return colour.XYZ_to_xy((self.x, self.y, self.z))

    @staticmethod
    def from_spectrum(spectrum):
        ''' computes XYZ coordinates from a spectrum

        Args:
            spectrum (`Spectrum`): a Spectrum object.

        Returns:
            `CIEXYZ`: a new CIEXYZ object.

        '''
        # we need colour
        check_colour()

        # convert to a spectral power distribution
        spectrum = normalize_spectrum(spectrum)
        spd = spd_from_spectrum(spectrum)

        # map onto correct wavelength pts
        standard_wavelengths = colour.SpectralShape(start=360, end=780, interval=10)
        xyz = colour.colorimetry.spectral_to_XYZ(spd.align(standard_wavelengths))
        return CIEXYZ(*xyz)

class CIELUV(object):
    ''' CIE 1976 color coordinate system.

    Notes:
        This is the CIE L* u' v' system, not LUV.
    '''

    def __init__(self, u, v, l=None):
        ''' Creates a new CIELUV instance

        Args:
            u (`float`): u coordinate

            v (`float`): v coordinate

            l (`float): l coordinate

        Returns:
            `CIELUV`: new CIELIV instance.

        '''
        self.u = u
        self.v = v
        self.l = l

    def to_uv(self):
        ''' Returns the u, v coordinates.
        '''
        return colour.Luv_to_uv((self.l, self.u, self.v))

    @staticmethod
    def from_XYZ(ciexyz=None, x=None, y=None, z=None):
        ''' Computes CIEL*u'v' coordinates from XYZ coordinate.

        Args:
            ciexyz (`CIEXYZ`): CIEXYZ object holding X,Y,Z coordinates.

            x (`float`): x coordinate.

            y (`float`): y coordinate.

            z (`float`): z coordinate.

        Returns:
            `CIELUV`: new CIELUV object.

        Notes:
            if given ciexyz object, x, y, and z are not used.  If given x, y, z,
            then ciexyz object is not needed.

        '''
        if ciexyz is not None:
            x, y, z = ciexyz.x, ciexyz.y, ciexyz.z
        elif x is None and y is None and z is None:
            raise ValueError('all values are None')

        l, u, v = colour.XYZ_to_Luv((x, y, z))
        return CIELUV(u, v, l)

    @staticmethod
    def from_spectrum(spectrum):
        ''' converts a spectrum to CIELUV coordinates.

        Args:
            spectrum (`Spectrum`): spectrum object to convert.

        Returns:
            `CIELUV`: new CIELUV object.

        '''
        xyz = CIEXYZ.from_spectrum(spectrum)
        return CIELUV.from_XYZ(xyz)

def normalize_spectrum(spectrum):
    ''' Normalizes a spectrum to have unit peak within the visible band.
    Args:
        spectrum (`Spectrum`): object with iterable wavelength, value fields.

    Returns:
        `Spectrum`: new spectrum object.

    '''
    wvl, vals = spectrum.wavelengths, spectrum.values
    low, high = np.searchsorted(wvl, 400), np.searchsorted(wvl, 700)
    vis_values_max = vals[low:high].max()
    return Spectrum(wvl, vals/vis_values_max)

def spd_from_spectrum(spectrum):
    ''' converts a spectrum to a colour spectral power distribution object.

    Args:
        spectrm (`Spectrum`): spectrum object to conver to spd.

    Returns:
        `SpectralPowerDistribution`: colour SPD object.

    '''
    spectrum_dict = dict(zip(spectrum.wavelengths, spectrum.values))
    return colour.SpectralPowerDistribution('', spectrum_dict)

def check_colour():
    ''' Checks if colour is available, raises if not.
    '''
    if 'colour' not in globals(): # or in locals
            raise ImportError('prysm colorimetry requires the colour package, '
                              'see http://colour-science.org/installation-guide/')

def cie_1976_plot(xlim=(0, 0.7), ylim=None, samples=200, fig=None, ax=None):
    ''' Creates a CIE 1976 plot.

    Args:

        xlim (`iterable`): left and right bounds of the plot.

        ylim (`iterable`): lower and upper bounds of the plot.  If `None`,
            the y bounds will be chosen to match the x bounds.

        samples (`int`): number of 1D samples within the region of interest,
            total pixels will be samples^2.

        fig (`matplotlib.figure.Figure`): figure to plot in.

        ax (`matplotlib.axes.Axis`): axis to plot in.

    Returns:
        `tuple` containing:

            `matplotlib.figure.Figure`: figure containing the plot.

            `matplotlib.axes.axis`: axis containing the plot.

    '''
    # duplicate xlim if ylim not set
    if ylim is None:
        ylim = xlim

    # generate a spectral locust and a mask based on it in u, v coordinates
    wvl = np.arange(400, 700, 10)
    wvl_XYZ = colour.wavelength_to_XYZ(wvl)
    wvl_u, wvl_v = XYZ_to_uv(wvl_XYZ)
    wvl_pts = np.stack((wvl_u, wvl_v), axis=1) * samples
    wvl_mask = generate_mask(wvl_pts, samples)
    mask_idxs = np.where(wvl_mask == 0)

    # generate a grid of u, v coordinates
    u = np.linspace(xlim[0], xlim[1], samples)
    v = np.linspace(ylim[0], ylim[1], samples)
    uu, vv = np.meshgrid(u, v)

    # regions outside of the spectral locust will cause color space transforms
    # to throw or warn, set them to NaN so numpy leaves them be
    uu[mask_idxs] = nan
    vv[mask_idxs] = nan
    shape = uu.shape

    # stack u and v for vectorized computations
    uuvv = np.stack((uu,vv), axis=len(shape))

    # map -> xy -> XYZ -> sRGB
    xy = Luv_uv_to_xy(uuvv)
    xyz = xy_to_XYZ(xy)
    colors = colour.XYZ_to_sRGB(xyz)
    fig, ax = share_fig_ax(fig, ax)

    return fig, ax

'''
    Below here are color space conversions ported from colour to make them numpy
    ufuncs supporting array vectorization.  For more information, see colour:
    https://github.com/colour-science/colour/
'''

def XYZ_to_xyY(XYZ):
    ''' Converts xyz points to xy points.

    Args:
        XYZ (`numpy.ndarray`): ndarray with first dimension corresponding to
            X, Y, Z.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: x coordinates.

            `numpy.ndarray`: y coordinates.

            `numpy.ndarray`: Y coordinates.

    '''
    X, Y, Z = XYZ[..., 0], XYZ[..., 1], XYZ[..., 2]

    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    Y = Y
    shape = x.shape
    return np.stack((x, y, Y), axis=len(shape))

def XYZ_to_xy(XYZ):
    ''' Converts XYZ points to xy points.

    Args:
        XYZ (`numpy.ndarray`): ndarray with first dimension corresponding to
            X, Y, Z.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: x coordinates.

            `numpy.ndarray`: y coordinates.

    '''
    xyY = XYZ_to_xyY(XYZ)
    return xyY_to_xy(xyY)

def XYZ_to_uv(XYZ):
    ''' Converts XYZ points to uv points.

    Args:
        XYZ (`numpy.ndarray`): ndarray with first dimension corresponding to
            X, Y, Z.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: u coordinates.

            `numpy.ndarray`: u coordinates.

    '''
    X, Y, Z = XYZ[..., 0], XYZ[..., 1], XYZ[..., 2]
    u = (4 * X) / (X + 15 * Y + 3 * Z)
    v = (9 * Y) / (X + 15 * Y + 3 * Z)

    shape = u.shape
    return np.stack((u, v), axis=len(shape))

def xyY_to_xy(xyY):
    ''' converts xyY points to xy points.

    Args:
        xyY (`numpy.ndarray`): ndarray with first dimension corresponding to
            x, y, Y.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: x coordinates.

            `numpy.ndarray`: y coordinates.

    '''
    shape = xyY.shape
    if shape[-1] is 2:
        return xyY
    else:
        x, y, Y = xyY

        shape = x.shape
        return np.stack((x, y), axis=len(shape))

def xyY_to_XYZ(xyY):
    ''' converts xyY points to XYZ points.

    Args:
        xyY (`numpy.ndarray`): ndarray with first dimension corresponding to
            x, y, Y.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: X coordinates.

            `numpy.ndarray`: Y coordinates.

            `numpy.ndarray`: Z coordinates.

    '''
    x, y, Y = xyY[..., 0], xyY[..., 1], xyY[..., 2]
    X = (x * Y) / y
    Y = Y
    Z = ((1 - x - y) * Y) / y

    shape = X.shape
    return np.stack((X, Y, Z), axis=len(shape))

def xy_to_xyY(xy, Y=1):
    ''' converts xy points to xyY points.

    Args:
        xy (`numpy.ndarray`): ndarray with first dimension corresponding to
            x, y.

        Y (`numpy.ndarray`): Y value to fill with.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: x coordinates.

            `numpy.ndarray`: y coordinates.

            `numpy.ndarray`: Y coordinates.

    '''
    shape = xy.shape
    if shape[-1] is 3:
        return xy
    else:
        x, y = xy[..., 0], xy[..., 1]
        Y = np.ones(x.shape) * Y

        shape = x.shape
        return np.stack((x, y, Y), axis=len(shape))

def xy_to_XYZ(xy):
    ''' converts xy points to xyY points.

    Args:
        xy (`numpy.ndarray`): ndarray with first dimension corresponding to
            x, y.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: X coordinates.

            `numpy.ndarray`: Y coordinates.

            `numpy.ndarray`: Z coordinates.

    '''
    xyY = xy_to_xyY(xy)
    return xyY_to_XYZ(xyY)

def Luv_to_XYZ(Luv):
    ''' Converts Luv points to XYZ points.

    Args:
        Luv (`numpy.ndarray`): ndarray with first dimension corresponding to
            L, u, v.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: X coordinates.

            `numpy.ndarray`: Y coordinates.

            'numpy.ndarray`: Z coordinates.

    '''
    L, u, v = Luv[..., 0], Luv[..., 1], Luv[..., 2]
    XYZ_D50 = [0.9642, 1.0000, 0.8251]
    X_r, Y_r, Z_r = XYZ_D50 # tsplit(xyY_to_XYZ(xy_to_xyY(illuminant)))

    Y = np.where(L > CIE_E * CIE_K, ((L + 16) / 116) ** 3, L / CIE_K)

    a = 1 / 3 * ((52 * L / (u + 13 * L * (4 * X_r /
                                          (X_r + 15 * Y_r + 3 * Z_r)))) - 1)
    b = -5 * Y
    c = -1 / 3.0
    d = Y * (39 * L / (v + 13 * L * (9 * Y_r /
                                     (X_r + 15 * Y_r + 3 * Z_r))) - 5)

    X = (d - b) / (a - c)
    Z = X * a + b

    shape = X.shape
    return np.stack((X, Y, Z), axis=len(shape))

def Luv_to_uv(Luv):
    ''' Converts Luv points to uv points.

    Args:
        Luv (`numpy.ndarray`): ndarray with first dimension corresponding to
            L, u, v.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: u coordinates.

            `numpy.ndarray`: v coordinates.

    '''
    XYZ = Luv_to_XYZ(Luv)
    return XYZ_to_uv(XYZ)

def Luv_uv_to_xy(uv):
    ''' Converts Luv u,v points to xyY x,y points.

    Args:
        uv (`numpy.ndarray`): ndarray with first dimension corresponding to
            u, v.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: x coordinates.

            `numpy.ndarray`: y coordinates.

    '''
    u, v = uv[..., 0], uv[..., 1]
    #u, v = v, u
    x = (9 * u) / (6 * u - 16 * v + 12)
    y = (4 * v) / (6 * u - 16 * v + 12)

    shape = x.shape
    return np.stack((x, y), axis=len(shape))

def XYZ_to_RGB(XYZ):
    ''' Converts xyz points to RGB points.

    Args:
        XYZ (`numpy.ndarray`): ndarray with first dimension corresponding to
            X, Y, Z.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: R coordinates.

            `numpy.ndarray`: G coordinates.

            `numpy.ndarray`: B coordinates.

    '''
    pass

def XYZ_to_sRGB(XYZ):
    ''' Converts xyz points to xy points.

    Args:
        XYZ (`numpy.ndarray`): ndarray with first dimension corresponding to
            X, Y, Z.

    Returns:
        `tuple` containing:

            `numpy.ndarray`: x coordinates.

            `numpy.ndarray`: y coordinates.

            `numpy.ndarray`: Y coordinates.

    '''
    pass