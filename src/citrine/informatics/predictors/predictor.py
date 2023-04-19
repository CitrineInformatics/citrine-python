from citrine._rest.asynchronous_object import AsynchronousObject

__all__ = ['Predictor']


class Predictor(AsynchronousObject):
    """Parent type of the individual PredictorNode and composite GraphPredictor."""

    _in_progress_statuses = ["VALIDATING", "CREATED"]
    _succeeded_statuses = ["READY"]
    _failed_statuses = ["INVALID", "ERROR"]
