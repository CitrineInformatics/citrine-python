import citrine.jobs.job
from citrine._utils.functions import shadow_classes_in_module
import sys


shadow_classes_in_module(citrine.jobs.job, sys.modules[__name__])
