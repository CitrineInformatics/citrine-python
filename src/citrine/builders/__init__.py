"""Tools for building custom SL assets client-side."""
from gemd.enumeration.base_enumeration import BaseEnumeration


class AutoConfigureMode(BaseEnumeration):
    """[ALPHA] The format to use in building auto-configured assets.

    * PLAIN corresponds to a single-row GEM table and plain predictor
    * FORMULATION corresponds to a multi-row GEM table and formulations predictor
    """

    PLAIN = "plain"
    FORMULATION = "formulation"
