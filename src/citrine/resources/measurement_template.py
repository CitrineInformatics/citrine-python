"""Resources that represent measurement templates."""
from collections.abc import Sequence

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import LinkOrElse, List, Object, Optional, \
    SpecifiedMixedList, Union
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.object_templates import ObjectTemplate, ObjectTemplateCollection
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.property_template import PropertyTemplate
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.measurement_template \
    import MeasurementTemplate as GEMDMeasurementTemplate
from gemd.entity.template.condition_template import ConditionTemplate as GEMDConditionTemplate
from gemd.entity.template.parameter_template import ParameterTemplate as GEMDParameterTemplate
from gemd.entity.template.property_template import PropertyTemplate as GEMDPropertyTemplate


class MeasurementTemplate(
    GEMDResource['MeasurementTemplate'],
    ObjectTemplate,
    GEMDMeasurementTemplate,
    typ=GEMDMeasurementTemplate.typ
):
    """
    A measurement template.

    Measurement templates are collections of condition, parameter and property templates that
    constrain the values of a measurement's condition, parameter and property attributes, and
    provide a common structure for describing similar measurements.

    Parameters
    ----------
    name: str
        The name of the measurement template.
    description: str, optional
        Long-form description of the measurement template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: list[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    conditions: list[ConditionTemplate] or list[ConditionTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated conditions. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this condition.
    parameters: list[ParameterTemplate] or list[ParameterTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated parameters. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this parameter.
    properties: list[PropertyTemplate] or list[PropertyTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated properties. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this property.

    """

    _response_key = GEMDMeasurementTemplate.typ  # 'measurement_template'

    properties = Optional(List(Union([LinkOrElse(GEMDPropertyTemplate),
                                      SpecifiedMixedList([LinkOrElse(GEMDPropertyTemplate),
                                                          Optional(Object(BaseBounds))])])),
                          'properties',
                          override=True)
    conditions = Optional(List(Union([LinkOrElse(GEMDConditionTemplate),
                                      SpecifiedMixedList([LinkOrElse(GEMDConditionTemplate),
                                                          Optional(Object(BaseBounds))])])),
                          'conditions',
                          override=True)
    parameters = Optional(List(Union([LinkOrElse(GEMDParameterTemplate),
                                      SpecifiedMixedList([LinkOrElse(GEMDParameterTemplate),
                                                          Optional(Object(BaseBounds))])])),
                          'parameters',
                          override=True)

    def __init__(self,
                 name: str,
                 *,
                 uids: dict[str, str] | None = None,
                 properties: Sequence[PropertyTemplate | LinkByUID
                                      | Sequence[PropertyTemplate | LinkByUID | BaseBounds | None]
                                      ] | None = None,
                 conditions: Sequence[ConditionTemplate | LinkByUID
                                      | Sequence[ConditionTemplate | LinkByUID | BaseBounds | None]
                                      ] | None = None,
                 parameters: Sequence[ParameterTemplate | LinkByUID
                                      | Sequence[ParameterTemplate | LinkByUID | BaseBounds | None]
                                      ] | None = None,
                 description: str | None = None,
                 tags: list[str] | None = None):
        if uids is None:
            uids = dict()
        super(ObjectTemplate, self).__init__()
        GEMDMeasurementTemplate.__init__(self, name=name, properties=properties,
                                         conditions=conditions, parameters=parameters, tags=tags,
                                         uids=uids, description=description)

    def __str__(self):
        return '<Measurement template {!r}>'.format(self.name)


class MeasurementTemplateCollection(ObjectTemplateCollection[MeasurementTemplate]):
    """A collection of measurement templates."""

    _individual_key = 'measurement_template'
    _collection_key = 'measurement_templates'
    _resource = MeasurementTemplate

    @classmethod
    def get_type(cls) -> type[MeasurementTemplate]:
        """Return the resource type in the collection."""
        return MeasurementTemplate
