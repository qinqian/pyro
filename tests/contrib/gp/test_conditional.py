from __future__ import absolute_import, division, print_function

from collections import namedtuple

import pytest
import torch

import pyro
from pyro.contrib.gp.kernels import WhiteNoise, Matern52
from pyro.contrib.gp.util import conditional
from tests.common import assert_equal

T = namedtuple("TestConditional", ["Xnew", "X", "kernel", "f_loc", "f_scale_tril",
                                   "loc", "cov"])

Xnew = torch.tensor([[2., 3.], [4., 6.]])
X = torch.tensor([[1., 5.], [2., 1.], [3., 2.]])
kernel = Matern52(input_dim=2)
Kff = kernel(X) + torch.eye(3) * 1e-6
Lff = Kff.potrf(upper=False)
pyro.set_rng_seed(123)
f_loc = torch.rand(3)
f_scale_tril = torch.rand(3, 3).tril(-1) + torch.rand(3).exp().diag()
f_cov = f_scale_tril.matmul(f_scale_tril.t())

TEST_CASES = [
    T(
        Xnew, X, kernel, torch.zeros(3), Lff, torch.zeros(2), None
    ),
    T(
        Xnew, X, kernel, torch.zeros(3), None, torch.zeros(2), None
    ),
    T(
        Xnew, X, kernel, f_loc, Lff, None, kernel(Xnew)
    ),
    T(
        X, X, kernel, f_loc, f_scale_tril, f_loc, f_cov
    ),
    T(
        X, X, kernel, f_loc, None, f_loc, torch.zeros(3, 3)
    ),
    T(
        Xnew, X, WhiteNoise(input_dim=2), f_loc, f_scale_tril, torch.zeros(2), torch.eye(2)
    ),
    T(
        Xnew, X, WhiteNoise(input_dim=2), f_loc, None, torch.zeros(2), torch.eye(2)
    ),
]

TEST_IDS = [str(i) for i in range(len(TEST_CASES))]


@pytest.mark.parametrize("Xnew, X, kernel, f_loc, f_scale_tril, loc, cov",
                         TEST_CASES, ids=TEST_IDS)
def test_conditional(Xnew, X, kernel, f_loc, f_scale_tril, loc, cov):
    loc0, cov0 = conditional(Xnew, X, kernel, f_loc, f_scale_tril, full_cov=True)
    loc1, var1 = conditional(Xnew, X, kernel, f_loc, f_scale_tril, full_cov=False)

    if loc is not None:
        assert_equal(loc0, loc)
        assert_equal(loc1, loc)
    n = cov0.shape[-1]
    var0 = torch.stack([mat.diag() for mat in cov0.view(-1, n, n)]).reshape(cov0.shape[:-1])
    assert_equal(var0, var1)
    if cov is not None:
        assert_equal(cov0, cov)