import inspect

import sys

import citrine.gemtables.variables as updated_module

current_module = sys.modules[__name__]
for c in [cls for _, cls in inspect.getmembers(updated_module, inspect.isclass) if
          cls.__module__ == updated_module.__name__]:
    setattr(current_module, c.__qualname__, c)
