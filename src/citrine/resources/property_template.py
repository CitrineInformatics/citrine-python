"""Resources that represent property templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import GEMDResource
from citrine.resources.attribute_templates import AttributeTemplate, AttributeTemplateCollection
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.template.property_template import PropertyTemplate as GEMDPropertyTemplate


class PropertyTemplate(
    GEMDResource['PropertyTemplate'],
    AttributeTemplate,
    GEMDPropertyTemplate,
    typ=GEMDPropertyTemplate.typ
):
    """
    A property template.

    Parameters
    ----------
    name: str
        The name of the property template.
    bounds: :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`
        Bounds circumscribe the values that are valid according to this property template.
    description: str, optional
        A long-form description of the property template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.

    """

    _response_key = GEMDPropertyTemplate.typ  # 'property_template'

    def __init__(self,
                 name: str,
                 *,
                 bounds: BaseBounds,
                 uids: Optional[Dict[str, str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        if uids is None:
            uids = dict()
        super(AttributeTemplate, self).__init__()
        GEMDPropertyTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                      uids=uids, description=description)

    def __str__(self):
        return '<Property template {!r}>'.format(self.name)


class PropertyTemplateCollection(AttributeTemplateCollection[PropertyTemplate]):
    """A collection of property templates."""

    _path_template = 'teams/{team_id}/datasets/{dataset_id}/property-templates'
    # During this "Projects in Teams" deprication `_path_template` is defined as a Class Variable whereas `_dataset_agnostic_path_template` is defined as a Class Property.
    # This allows for either path to be accessed depending on the user's instantiation of the class.
    # Post-deprication, both can be Class Variables again, using the `teams/...` path.
    _individual_key = 'property_template'
    _collection_key = 'property_templates'
    _resource = PropertyTemplate

    @property
    def _dataset_agnostic_path_template(self):
        if self.project_id is None:
            return 'teams/{self.team_id}/property-templates'
        else:
            return 'projects/{self.project_id}/property-templates'

    @classmethod
    def get_type(cls) -> Type[PropertyTemplate]:
        """Return the resource type in the collection."""
        return PropertyTemplate
