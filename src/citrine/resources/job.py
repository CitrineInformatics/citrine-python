import sys

import citrine.jobs.job
from citrine.jobs.job import _poll_for_job_completion  # noqa
from citrine._utils.functions import shadow_classes_in_module

shadow_classes_in_module(citrine.jobs.job, sys.modules[__name__])
