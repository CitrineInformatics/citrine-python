from citrine._serialization import properties
from citrine._serialization.serializable import Serializable


class SampleDesignSpaceInput(Serializable['SampleDesignSpaceInput']):
    """A Citrine Sample Design Space Execution Input.

    Parameters
    ----------
    n_candidates: int
        The number of non-correlated samples to draw from the design space domain.

    """

    n_candidates = properties.Integer("n_candidates")

    def __init__(self, *, n_candidates: int):
        self.n_candidates: int = n_candidates
