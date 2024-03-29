"""Top-level class for all data object (i.e., spec and run) objects and collections thereof."""
from abc import ABC
from typing import Dict, Union, Optional, Iterator, List, TypeVar
from uuid import uuid4

from gemd.json import GEMDJson
from gemd.util import recursive_foreach

from citrine._utils.functions import get_object_id, replace_objects_with_links, scrub_none
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import String, Object
from citrine._serialization.properties import Optional as PropertyOptional
from gemd.entity.file_link import FileLink
from citrine.exceptions import BadRequest
from citrine.resources.api_error import ValidationError
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.object_templates import ObjectTemplateResourceType
from citrine.resources.process_template import ProcessTemplate
from gemd.entity.object.base_object import BaseObject
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.attribute_template import AttributeTemplate


class DataObject(DataConcepts, BaseObject, ABC):
    """
    An abstract data object object.

    DataObject must be extended along with `Resource`
    """

    notes = PropertyOptional(String(), 'notes')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links', override=True)


DataObjectResourceType = TypeVar("DataObjectResourceType", bound="DataObject")


class DataObjectCollection(DataConceptsCollection[DataObjectResourceType], ABC):
    """A collection of one kind of data object object."""

    def list_by_attribute_bounds(
            self,
            attribute_bounds: Dict[Union[AttributeTemplate, LinkByUID], BaseBounds], *,
            forward: bool = True, per_page: int = 100) -> Iterator[DataObject]:
        """
        Get all objects in the collection with attributes within certain bounds.

        Results are ordered first by dataset, then by attribute value.

        Currently only one attribute and one bounds on that attribute is supported, and
        attribute type must be numeric.

        Parameters
        ----------
        attribute_bounds: Dict[Union[AttributeTemplate, \
        :py:class:`LinkByUID <gemd.entity.link_by_uid.LinkByUID>`], \
        :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`]
            A dictionary from attributes to the bounds on that attribute.
            Currently only real and integer bounds are supported.
            Each attribute may be represented as an AttributeTemplate (PropertyTemplate,
            ParameterTemplate, or ConditionTemplate) or as a LinkByUID,
            but in either case there must be a uid and it must correspond to an
            AttributeTemplate that exists in the database.
            Only the uid is passed, so if you would like to update an attribute template you
            must register that change to the database before you can use it to filter.
        forward: bool
            Set to False to reverse the order of results (i.e., return in descending order).
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[DataObject]
            List of every object in this collection whose `name` matches the search term.

        """
        body = self._get_attribute_bounds_search_body(attribute_bounds)
        params = {}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        raw_objects = self.session.cursor_paged_resource(
            self.session.post_resource,
            # "Ignoring" dataset because it is in the query params (and required)
            self._get_path(ignore_dataset=True, action="filter-by-attribute-bounds"),
            json=body,
            forward=forward,
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    @staticmethod
    def _get_attribute_bounds_search_body(attribute_bounds):
        if not isinstance(attribute_bounds, dict):
            raise TypeError('attribute_bounds must be a dict mapping template to bounds; '
                            'got {}'.format(attribute_bounds))
        if len(attribute_bounds) != 1:
            raise NotImplementedError('Currently, only searches with exactly one template '
                                      'to bounds mapping are supported; got {}'
                                      .format(attribute_bounds))
        return {
            'attribute_bounds': {
                get_object_id(templ): bounds.as_dict()
                for templ, bounds in attribute_bounds.items()
            }
        }

    def validate_templates(self, *,
                           model: DataObjectResourceType,
                           object_template: Optional[ObjectTemplateResourceType] = None,
                           ingredient_process_template: Optional[ProcessTemplate] = None)\
            -> List[ValidationError]:
        """
        Validate a data object against its templates.

        Validates against provided object templates (passed in as parameters) and stored attribute
        templates linked on the data object.

        :param model: the data object to validate
        :param object_template: optional object template to validate against
        :param ingredient_process_template: optional process template to validate ingredient
         against. Ignored unless data object is an IngredientSpec or IngredientRun.
        :return: List[ValidationError] of validation errors encountered. Empty if successful.
        """
        path = self._get_path(ignore_dataset=True, action="validate-templates")

        temp_scope = str(uuid4())
        GEMDJson(scope=temp_scope).dumps(model)  # This apparent no-op populates uids
        dumped_data = replace_objects_with_links(scrub_none(model.dump()))
        recursive_foreach(model, lambda x: x.uids.pop(temp_scope, None))  # Strip temp uids

        request_data = {"dataObject": dumped_data}
        if object_template is not None:
            request_data["objectTemplate"] = \
                replace_objects_with_links(scrub_none(object_template.dump()))
        if ingredient_process_template is not None:
            request_data["ingredientProcessTemplate"] = \
                replace_objects_with_links(scrub_none(ingredient_process_template.dump()))
        try:
            self.session.put_resource(path, request_data)
            return []
        except BadRequest as e:
            if e.api_error is not None and e.api_error.validation_errors:
                return e.api_error.validation_errors
            raise e
