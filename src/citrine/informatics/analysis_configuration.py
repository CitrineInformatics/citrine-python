"""Settings for working Analysis workflows"""
from typing import Optional, List

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties


class CrossValidationAnalysisConfiguration(Serializable['CrossValidationAnalysisConfiguration']):

    name = properties.String('name')
    description = properties.String('description')
    n_folds = properties.Integer('n_folds')
    n_trials = properties.Integer('n_trials')
    seed = properties.Optional(properties.Integer, 'seed')
    group_by_keys = properties.Optional(properties.List(properties.String), 'group_by_keys')
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
    ):
        self.name = name
        self.description = description
        self.n_folds = n_folds
        self.n_trials = n_trials
        self.seed = seed
        self.group_by_keys = group_by_keys
        self.max_rows = max_rows