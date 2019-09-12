"""A resource that represents a parameter attribute."""
from typing import Optional, List

from citrine._serialization.properties import String, Object, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import DataConcepts
from taurus.entity.attribute.parameter import Parameter as TaurusParameter
from taurus.entity.value.base_value import BaseValue
from taurus.entity.file_link import FileLink
from taurus.entity.template.parameter_template import ParameterTemplate as TaurusParameterTemplate


class Parameter(DataConcepts, Serializable['Parameter'], TaurusParameter):
    """
    A parameter attribute.

    Parameters are the non-environmental variables (typically specified and controlled) that may
    affect a process or measurement: e.g. oven dial temperature for a kiln firing, magnification
    for a measurement taken with an electron microscope.

    Parameters
    ----------
    name: str
        Required name of the parameter. Each parameter within an object must have a unique name.
    notes: str
        Optional free-form notes about the parameter.
    value: :py:class:`BaseValue <taurus.entity.value.base_value.BaseValue>`
        The value of the parameter.
    template: :class:`ParameterTemplate <citrine.resources.parameter_template.ParameterTemplate>`
        Parameter template that defines the allowed bounds of this parameter. If a template
        and value are both present then the value must be within the template bounds.
    origin: str
        The origin of the parameter. Must be one of "measured", "predicted", "summary",
        "specified", "computed", or "unknown." Default is "unknown."
    file_links: List[FileLink]
        Links to files associated with the parameter.

    """

    _response_key = TaurusParameter.typ  # 'parameter'

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
                 template: Optional[TaurusParameterTemplate] = None,
                 origin: Optional[str] = "unknown",
                 file_links: Optional[List[FileLink]] = None):
        TaurusParameter.__init__(self, name=name, notes=notes, value=value, template=template,
                                 origin=origin, file_links=file_links)

    def __str__(self):
        return '<Parameter {!r}>'.format(self.name)
