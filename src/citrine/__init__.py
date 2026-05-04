"""
Citrine.io Python Client.

Documentation:
https://citrineinformatics.github.io/citrine-python/index.html

"""
import warnings

from citrine.citrine import Citrine  # noqa: F401
from .__version__ import __version__  # noqa: F401

# Python's default warning filter hides DeprecationWarning unless triggered from
# __main__ (PEP 565). Surface DeprecationWarnings raised from citrine.* so users
# see them before the deprecated APIs are removed.
warnings.filterwarnings("default", category=DeprecationWarning, module=r"citrine(\.|$)")
