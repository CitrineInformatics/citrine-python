"""Resources that represent ingredient run data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine.resources.data_concepts import DataConceptsCollection, DataConcepts
from citrine._serialization.properties import Mapping, String, LinkOrElse, Object
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from taurus.entity.file_link import FileLink
from taurus.entity.object.ingredient_run import IngredientRun as TaurusIngredientRun
from taurus.entity.object.ingredient_spec import IngredientSpec as TaurusIngredientSpec
from taurus.entity.object.material_run import MaterialRun as TaurusMaterialRun
from taurus.entity.value.continuous_value import ContinuousValue


class IngredientRun(DataConcepts, Resource['IngredientRun'], TaurusIngredientRun):
    """
    An ingredient run.

    Ingredients annotate a material with information about its usage in a process.

    Parameters
    ----------
    uids: Map[str, str], optional
        A collection of unique identifiers, each a key-value pair. The key is the "scope"
        and the value is the identifier. The scope "id" is reserved for the internal Citrine ID,
        which will always be a uuid4.
    tags: List[str], optional
        A set of tags. Tags can be used for filtering.
    notes: str, optional
        Long-form notes about the ingredient run.
    material: MaterialRun
        Material that this ingredient is.
    mass_fraction: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The mass fraction of the ingredient in the process.
    volume_fraction: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The volume fraction of the ingredient in the process.
    number_fraction: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The number fraction of the ingredient in the process.
    absolute_quantity: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The absolute quantity of the ingredient in the process.
    unique_label: str, optional
        Label on the ingredient that is unique within the process that contains it.
    labels: List[str], optional
        Additional labels on the ingredient that must be unique.
    spec: IngredientSpec
        The specification of which this ingredient is a realization.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = TaurusIngredientRun.typ  # 'ingredient_run'

    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    material = PropertyOptional(LinkOrElse(), 'material')
    mass_fraction = PropertyOptional(Object(ContinuousValue), 'mass_fraction')
    volume_fraction = PropertyOptional(Object(ContinuousValue), 'volume_fraction')
    number_fraction = PropertyOptional(Object(ContinuousValue), 'number_fraction')
    absolute_quantity = PropertyOptional(
        Object(ContinuousValue), 'absolute_quantity')
    unique_label = PropertyOptional(String(), 'unique_label')
    labels = PropertyOptional(PropertyList(String()), 'labels')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 material: Optional[TaurusMaterialRun] = None,
                 mass_fraction: Optional[ContinuousValue] = None,
                 volume_fraction: Optional[ContinuousValue] = None,
                 number_fraction: Optional[ContinuousValue] = None,
                 absolute_quantity: Optional[ContinuousValue] = None,
                 unique_label: Optional[str] = None,
                 labels: Optional[List[str]] = None,
                 spec: Optional[TaurusIngredientSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusIngredientRun.typ)
        TaurusIngredientRun.__init__(self, uids=set_default_uid(uids), tags=tags, notes=notes,
                                     material=material, mass_fraction=mass_fraction,
                                     volume_fraction=volume_fraction,
                                     number_fraction=number_fraction,
                                     absolute_quantity=absolute_quantity, labels=labels,
                                     unique_label=unique_label, spec=spec, file_links=file_links)

    def __str__(self):
        return '<Ingredient run {!r}>'.format(self.unique_label)


class IngredientRunCollection(DataConceptsCollection[IngredientRun]):
    """Represents the collection of all ingredient runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/ingredient-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/ingredient-runs'
    _individual_key = 'ingredient_run'
    _collection_key = 'ingredient_runs'

    @classmethod
    def get_type(cls) -> Type[IngredientRun]:
        """Return the resource type in the collection."""
        return IngredientRun
