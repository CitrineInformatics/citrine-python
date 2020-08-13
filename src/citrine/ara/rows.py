import sys

import citrine.gemtables.rows
from citrine._utils.functions import shadow_classes_in_module

shadow_classes_in_module(citrine.gemtables.rows, sys.modules[__name__])
