import sys

import citrine.gemtables.variables as variables_module
from citrine._utils.functions import shadow_classes_in_module

shadow_classes_in_module(variables_module, sys.modules[__name__])
