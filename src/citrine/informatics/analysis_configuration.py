"""Settings for working Analysis workflows."""
from typing import Optional, List
from warnings import warn

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties
from citrine.informatics.predictor_evaluator import CrossValidationEvaluator


class CrossValidationAnalysisConfiguration(Serializable['CrossValidationAnalysisConfiguration']):
    """[ALPHA] Configuration settings for running cross-validation in a performance workflow.

    Parameters
    ----------
    name : str
        Name of the analysis configuration
    description: str
        Description of the analysis configuration
    n_folds: int
        Number of folds
    n_trials: int
        Number of cross-validation trials to run, each with ``n_folds`` folds
    max_rows: int
        Maximum number of training candidates to use during cross-validation
    seed: int, optional
        Seed used to generate random test/train splits.
        If not provided, a random seed is used.
    group_by_keys: List[str], optional
        Set of keys used to group candidates.
        If present, candidates are grouped by the hash of
        ``(key, value)`` pairs computed on the given keys.
        If not provided, candidates are not grouped.
    responses: List[str], optional
        Set of descriptor keys to cross-validate.
        All requested responses must be present as an output of the predictor being analyzed.
        If not provided cross-validation metrics will be computed for all predictor responses.
        These cross-validated responses are removed from the data during the analysis,
        so which responses are requested can affect the performance metrics if the predictor
        contains latent variables. For example, if only the final output (leaf) responses are
        requested, latent variables are not removed during cross-validation. In this case the
        actual (and not predicted) values for latent variables are fed into the models used
        to compute leaf responses. Often this will manifest as a lower model error for the
        final response, compared to the model error computed when latent variables are requested
        and hence removed from the data. Note, if no responses are specified all leaf and
        latent variables are removed from the data during cross-validation.

    """

    name = properties.String('name')
    description = properties.String('description')
    n_folds = properties.Integer('n_folds')
    n_trials = properties.Integer('n_trials')
    seed = properties.Optional(properties.Integer, 'seed')
    group_by_keys = properties.Optional(properties.List(properties.String), 'group_by_keys')
    responses = properties.Optional(properties.List(properties.String), 'responses')
    max_rows = properties.Integer('max_rows')
    typ = properties.String('type', default='CrossValidationAnalysis', deserializable=False)

    def __init__(
            self,
            name: str,
            description: str,
            n_folds: int,
            n_trials: int,
            max_rows: int,
            seed: Optional[int] = None,
            group_by_keys: Optional[List[str]] = None,
            responses: Optional[List[str]] = None,
    ):
        warn("{this_class} is deprecated. Please use {replacement} instead".format(
            this_class=self.__class__.name, replacement=CrossValidationEvaluator.__name__))
        self.name = name
        self.description = description
        self.n_folds = n_folds
        self.n_trials = n_trials
        self.seed = seed
        self.group_by_keys = group_by_keys
        self.max_rows = max_rows
        self.responses = responses
