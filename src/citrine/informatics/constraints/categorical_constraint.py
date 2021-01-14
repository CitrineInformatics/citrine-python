from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints.constraint import Constraint

__all__ = ['CategoricalConstraint']


class CategoricalConstraint(Serializable['CategoricalConstraint'], Constraint):
    """
    [ALPHA] A constraint on a categorical material attribute to be in a set of acceptable values.

    Parameters
    ----------
    descriptor_key: str
        the key corresponding to the associated Categorical descriptor
    acceptable_categories: list[str]
        the names of the acceptable categories to constrain to

    """

    descriptor_key = properties.String('descriptor_key')
    acceptable_categories = properties.List(properties.String(), 'acceptable_classes')
    typ = properties.String('type', default='AcceptableCategoriesConstraint')

    def __init__(self,
                 descriptor_key: str,
                 acceptable_categories: List[str],
                 session: Optional[Session] = None):
        self.descriptor_key = descriptor_key
        self.acceptable_categories = acceptable_categories
        self.session = session

    def __str__(self):
        return '<CategoricalConstraint {!r}>'.format(self.descriptor_key)
