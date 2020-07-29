from citrine._utils.functions import shadow_classes_in_module

import sys
import citrine.gemtables.columns as columns_module

shadow_classes_in_module(columns_module, sys.modules[__name__])
