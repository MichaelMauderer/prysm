''' Unit tests for utility functions
'''
import pytest

import numpy as np

from prysm import util

ARR_SIZE = 32


@pytest.mark.parametrize('num', [1, 3, 5, 7, 9, 11, 13, 15, 991, 100000000000001])
def test_is_odd_odd_numbers(num):
    assert util.is_odd(num)


@pytest.mark.parametrize('num', [0, 2, 4, 6, 8, 10, 12, 14, 1000, 100000000000000])
def test_is_odd_even_numbers(num):
    assert not util.is_odd(num)


@pytest.mark.parametrize('num', [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192])
def test_is_power_of_2_powers_of_2(num):
    assert util.is_power_of_2(num)


@pytest.mark.parametrize('num', [1, 3, 5, 7, 1000, -2])
def test_is_power_of_2_non_powers_of_2(num):
    assert not util.is_power_of_2(num)


def test_rms_is_zero_for_single_value_array():
    arr = np.ones((ARR_SIZE, ARR_SIZE))
    assert util.rms(arr) == pytest.approx(1)


def test_ecdf_binary_distribution():
    x = np.asarray([0, 0, 0, 1, 1, 1])
    x, y = util.ecdf(x)
    assert np.allclose(np.unique(x), np.asarray([0, 1]))  # TODO: more rigorous tests.


@pytest.fixture(params=['flat', 'hanning', 'hamming', 'bartlett', 'blackman'])
def window(request):
    return request.param


@pytest.mark.parametrize('val', [-1, 1, 1.05])
def test_smooth_doesnt_change_constant_arrays(val, window):
    arr = np.ones((ARR_SIZE)) * val
    assert np.allclose(util.smooth(arr, window=window), arr)


def test_smooth_rejects_2d():
    arr = np.empty((2, 2))
    with pytest.raises(ValueError):
        util.smooth(arr)


def test_smooth_rejects_wrong_window():
    with pytest.raises(ValueError):
        arr = np.empty(4)
        util.smooth(arr, window='foo')


def test_smooth_rejects_window_bigger_than_array():
    window_length = 5
    arr_len = 2
    arr = np.empty((arr_len))
    with pytest.raises(ValueError):
        util.smooth(arr, window_len=window_length)


def test_correct_gamma_unity_case():
    arr = np.ones((ARR_SIZE, ARR_SIZE)) * 0.75
    out = util.correct_gamma(arr, encoding=1)
    assert np.allclose(arr, out)


def test_correct_gamma_general_case():
    arr = np.ones((ARR_SIZE, ARR_SIZE)) * 0.5
    out = util.correct_gamma(arr, encoding=0.5)
    assert np.allclose(arr**2, out)


def test_fold_array_function():
    arr = np.ones((ARR_SIZE, ARR_SIZE))
    assert util.fold_array(arr).all()
    assert util.fold_array(arr, axis=0).all()


@pytest.mark.parametrize('dzeta', [1 / 128.0, 1 / 256.0, 11.123 / 128.0, 1e10 / 2048.0])
def test_psf_to_pupil_sample_inverts_pupil_to_psf_sample(dzeta):
    samples, wvl, efl = 128, 0.55, 10
    psf_sample = util.pupil_sample_to_psf_sample(dzeta, samples, wvl, efl)
    assert util.psf_sample_to_pupil_sample(psf_sample, samples, wvl, efl) == dzeta


def test_guarantee_array_functionality():
    a_float = 5.0
    an_int = 10
    a_str = 'foo'
    an_array = np.empty(1)
    assert util.guarantee_array(a_float)
    assert util.guarantee_array(an_int)
    assert util.guarantee_array(an_array)
    with pytest.raises(ValueError):
        util.guarantee_array(a_str)


def test_sort_xy():
    x = np.linspace(10, 0, 10)
    y = np.linspace(1, 10, 10)
    xx, yy = util.sort_xy(x, y)
    assert xx == tuple(reversed(x))
    assert yy == tuple(reversed(y))


def test_colorline_functions():
    npts = 10
    x = np.linspace(0, 10, npts)
    y = np.ones(npts)

    assert util.colorline(x, y)
