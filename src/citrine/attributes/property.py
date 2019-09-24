"""A resource that represents a property attribute."""
from typing import Optional, List

from citrine._serialization.properties import String, Object, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import DataConcepts
from taurus.entity.attribute.property import Property as TaurusProperty
from taurus.entity.value.base_value import BaseValue
from taurus.entity.file_link import FileLink
from taurus.entity.template.property_template import PropertyTemplate as TaurusPropertyTemplate


class Property(DataConcepts, Serializable['Property'], TaurusProperty):
    """
    A property attribute.

    Properties are characteristics of a material that could be measured, e.g. chemical composition,
     density, yield strength.


    Parameters
    ----------
    name: str
        Required name of the property. Each property within an object must have a unique name.
    notes: str
        Optional free-form notes about the property.
    value: :py:class:`BaseValue <taurus.entity.value.base_value.BaseValue>`
        The value of the property.
    template: :class:`PropertyTemplate <citrine.resources.property_template.PropertyTemplate>`
        Property template that defines the allowed bounds of this property. If a template
        and value are both present then the value must be within the template bounds.
    origin: str
        The origin of the property. Must be one of "measured", "predicted", "summary",
        "specified", "computed", or "unknown." Default is "unknown."
    file_links: List[FileLink]
        Links to files associated with the property.

    """

    _response_key = TaurusProperty.typ  # 'property'

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
                 template: Optional[TaurusPropertyTemplate] = None,
                 origin: Optional[str] = "unknown",
                 file_links: Optional[List[FileLink]] = None):
        TaurusProperty.__init__(self, name=name, notes=notes, value=value, template=template,
                                origin=origin, file_links=file_links)

    def __str__(self):
        return '<Property {!r}>'.format(self.name)
