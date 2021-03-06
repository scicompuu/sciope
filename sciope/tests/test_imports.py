def test_data():
    from sciope.data import dataset


def test_designs():
    from sciope.designs import initial_design_base, factorial_design, latin_hypercube_sampling, random_sampling


def test_features():
    from sciope.features import feature_extraction


def test_inference():
    from sciope.inference import abc_inference, bandits_abc, inference_base


def test_models():
    from sciope.models import ann_regressor, gp_regressor, label_propagation, model_base


def test_sampling():
    from sciope.sampling import maximin_sampling, sampling_base


def test_visualize():
    from sciope.visualize import interactive_scatter


def test_utilities():
    from sciope.utilities.distancefunctions import distance_base, euclidean, manhattan, naive_squared
    from sciope.utilities.housekeeping import sciope_logger, sciope_profiler
    from sciope.utilities.mab import mab_base, mab_direct, mab_halving, mab_incremental, mab_sar
    from sciope.utilities.priors import prior_base, uniform_prior
    from sciope.utilities.summarystats import burstiness, global_max, global_min, summary_base, temporal_mean, \
        temporal_variance
