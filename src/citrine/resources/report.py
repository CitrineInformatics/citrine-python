import citrine.informatics.report
from citrine._utils.functions import shadow_classes_in_module
import sys


shadow_classes_in_module(citrine.informatics.report, sys.modules[__name__])
