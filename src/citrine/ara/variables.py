import sys

import citrine.gemtables.variables
from citrine._utils.functions import shadow_classes_in_module

shadow_classes_in_module(citrine.gemtables.variables, sys.modules[__name__])
