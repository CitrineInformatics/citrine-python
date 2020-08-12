from citrine._utils.functions import shadow_classes_in_module

import sys
import citrine.gemtables.columns

shadow_classes_in_module(citrine.gemtables.columns, sys.modules[__name__])
