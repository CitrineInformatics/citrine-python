"""A resource that represents a condition attribute."""
from typing import Optional, List

from citrine._serialization.properties import String, Object, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import DataConcepts
from taurus.entity.attribute.condition import Condition as TaurusCondition
from taurus.entity.value.base_value import BaseValue
from taurus.entity.file_link import FileLink
from taurus.entity.template.condition_template import ConditionTemplate as TaurusConditionTemplate


class Condition(DataConcepts, Serializable['Condition'], TaurusCondition):
    """
    A condition attribute.

    Conditions are environmental variables (typically measured) that may affect a process
    or measurement: e.g., temperature, pressure.

    Parameters
    ----------
    name: str
        Required name of the condition. Each condition within an object must have a unique name.
    notes: str
        Optional free-form notes about the condition.
    value: :py:class:`BaseValue <taurus.entity.value.base_value.BaseValue>`
        The value of the condition.
    template: :class:`ConditionTemplate <citrine.resources.condition_template.ConditionTemplate>`
        Condition template that defines the allowed bounds of this condition. If a template
        and value are both present then the value must be within the template bounds.
    origin: str
        The origin of the condition. Must be one of "measured", "predicted", "summary",
        "specified", "computed", or "unknown." Default is "unknown."
    file_links: List[FileLink]
        Links to files associated with the condition.

    """

    _response_key = TaurusCondition.typ  # 'condition'

    name = String('name')
    notes = PropertyOptional(String(), 'notes')
    value = PropertyOptional(Object(BaseValue), 'value')
    template = PropertyOptional(LinkOrElse(), 'template')
    origin = PropertyOptional(String(), 'origin', default='unknown')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type', default=_response_key, deserializable=False)

    def __init__(self,
                 name: str,
                 notes: Optional[str] = None,
                 value: Optional[BaseValue] = None,
                 template: Optional[TaurusConditionTemplate] = None,
                 origin: Optional[str] = "unknown",
                 file_links: Optional[List[FileLink]] = None):
        TaurusCondition.__init__(self, name=name, notes=notes, value=value, template=template,
                                 origin=origin, file_links=file_links)

    def __str__(self):
        return '<Condition {!r}>'.format(self.name)
