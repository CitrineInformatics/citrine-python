# TODO: Add a docstring here
from citrine.citrine import Citrine  # noqa: F401
import logging
import warnings
from .__version__ import __version__  # noqa: F401

logging.basicConfig(level=logging.WARNING)
warnings.simplefilter("default", DeprecationWarning)
