"""Record to hold branch data version update information."""
from typing import List

from citrine._rest.resource import PredictorRef, Resource
from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable


class DataVersionUpdate(Serializable['DataVersionUpdate']):
    """ Container for data updates. """

    current = _properties.String('current')
    latest = _properties.String('latest')

    def __init__(self,
                 current: str,
                 latest: str):
        self.current = current
        self.latest = latest

    typ = _properties.String('type', default='DataVersionUpdate')


class BranchDataUpdate(Resource['BranchDataUpdate']):
    """
    Branch data updates with predictors using the versions indicated that
    are in READY status.
    """

    data_updates = _properties.List(_properties.Object(DataVersionUpdate), "data_updates")
    predictors = _properties.List(_properties.Object(PredictorRef), "predictors")

    def __init__(self,
                 data_updates: List[DataVersionUpdate],
                 predictors: List[PredictorRef]):
        self.data_updates = data_updates
        self.predictors = predictors


class NextBranchVersionRequest(Resource['NextBranchVersionRequest']):
    """
    Instructions for how the next version of a branch should handle its predictors when the
    workflows are cloned.

    data_updates contains the list of data source versions to upgrade
    (current->latest), and use_predictors will wither have a <predictor_id>:latest to indicate
    the workflow should use a new version of the predictor.  Or <predictor_id>:<version #> to
    indicate that the workflow should use an existing predictor version.
    """

    data_updates = _properties.List(_properties.Object(DataVersionUpdate), "data_updates")
    use_predictors = _properties.List(_properties.Object(PredictorRef), "use_predictors")

    def __init__(self,
                 data_updates: List[DataVersionUpdate],
                 use_predictors: List[PredictorRef]):
        self.data_updates = data_updates
        self.use_predictors = use_predictors
