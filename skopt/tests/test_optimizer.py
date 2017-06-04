import numpy as np
import pytest

from sklearn.utils.testing import assert_equal
from sklearn.utils.testing import assert_raises

from skopt.benchmarks import bench1
from skopt.learning import ExtraTreesRegressor, RandomForestRegressor
from skopt.learning import GradientBoostingQuantileRegressor
from skopt.optimizer import Optimizer
from scipy.optimize import OptimizeResult


TREE_REGRESSORS = (ExtraTreesRegressor(random_state=2),
                   RandomForestRegressor(random_state=2),
                   GradientBoostingQuantileRegressor(random_state=2))


@pytest.mark.fast_test
def test_multiple_asks():
    # calling ask() multiple times without a tell() inbetween should
    # be a "no op"
    base_estimator = ExtraTreesRegressor(random_state=2)
    opt = Optimizer([(-2.0, 2.0)], base_estimator, n_random_starts=1,
                    acq_optimizer="sampling")

    opt.run(bench1, n_iter=3)
    # tell() computes the next point ready for the next call to ask()
    # hence there are three after three iterations
    assert_equal(len(opt.models), 3)
    assert_equal(len(opt.Xi), 3)
    opt.ask()
    assert_equal(len(opt.models), 3)
    assert_equal(len(opt.Xi), 3)
    assert_equal(opt.ask(), opt.ask())


@pytest.mark.fast_test
def test_invalid_tell_arguments():
    base_estimator = ExtraTreesRegressor(random_state=2)
    opt = Optimizer([(-2.0, 2.0)], base_estimator, n_random_starts=1,
                    acq_optimizer="sampling")

    # can't have single point and multiple values for y
    assert_raises(ValueError, opt.tell, [1.], [1., 1.])


@pytest.mark.fast_test
def test_bounds_checking_1D():
    low = -2.
    high = 2.
    base_estimator = ExtraTreesRegressor(random_state=2)
    opt = Optimizer([(low, high)], base_estimator, n_random_starts=1,
                    acq_optimizer="sampling")

    assert_raises(ValueError, opt.tell, [high + 0.5], 2.)
    assert_raises(ValueError, opt.tell, [low - 0.5], 2.)
    # feed two points to tell() at once
    assert_raises(ValueError, opt.tell, [high + 0.5, high], (2., 3.))
    assert_raises(ValueError, opt.tell, [low - 0.5, high], (2., 3.))


@pytest.mark.fast_test
def test_bounds_checking_2D():
    low = -2.
    high = 2.
    base_estimator = ExtraTreesRegressor(random_state=2)
    opt = Optimizer([(low, high), (low+4, high+4)], base_estimator,
                    n_random_starts=1, acq_optimizer="sampling")

    assert_raises(ValueError, opt.tell, [high + 0.5, high + 4.5], 2.)
    assert_raises(ValueError, opt.tell, [low - 0.5, low - 4.5], 2.)

    # first out, second in
    assert_raises(ValueError, opt.tell, [high + 0.5, high + 0.5], 2.)
    assert_raises(ValueError, opt.tell, [low - 0.5, high + 0.5], 2.)


@pytest.mark.fast_test
def test_bounds_checking_2D_multiple_points():
    low = -2.
    high = 2.
    base_estimator = ExtraTreesRegressor(random_state=2)
    opt = Optimizer([(low, high), (low+4, high+4)], base_estimator,
                    n_random_starts=1, acq_optimizer="sampling")

    # first component out, second in
    assert_raises(ValueError, opt.tell,
                  [(high + 0.5, high + 0.5), (high + 0.5, high + 0.5)],
                  [2., 3.])
    assert_raises(ValueError, opt.tell,
                  [(low - 0.5, high + 0.5), (low - 0.5, high + 0.5)],
                  [2., 3.])


@pytest.mark.fast_test
def test_returns_result_object():
    base_estimator = ExtraTreesRegressor(random_state=2)
    opt = Optimizer([(-2.0, 2.0)], base_estimator, n_random_starts=1,
                    acq_optimizer="sampling")
    result = opt.tell([1.5], 2.)

    assert isinstance(result, OptimizeResult)
    assert_equal(len(result.x_iters), len(result.func_vals))
    assert_equal(np.min(result.func_vals), result.fun)


@pytest.mark.fast_test
@pytest.mark.parametrize("base_estimator", TREE_REGRESSORS)
def test_acq_optimizer(base_estimator):
    with pytest.raises(ValueError) as e:
        opt = Optimizer([(-2.0, 2.0)], base_estimator=base_estimator,
                        n_random_starts=1, acq_optimizer='lbfgs')
    assert 'The tree-based regressor' in str(e.value)
