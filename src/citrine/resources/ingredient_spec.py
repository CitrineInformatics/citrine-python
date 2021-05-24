"""Resources that represent ingredient spec data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Mapping, String, LinkOrElse, Object
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts, CITRINE_SCOPE
from citrine.resources.object_specs import ObjectSpec, ObjectSpecCollection
from gemd.entity.file_link import FileLink
from gemd.entity.object.ingredient_spec import IngredientSpec as GEMDIngredientSpec
from gemd.entity.object.material_spec import MaterialSpec as GEMDMaterialSpec
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.value.continuous_value import ContinuousValue


class IngredientSpec(ObjectSpec, Resource['IngredientSpec'], GEMDIngredientSpec):
    """
    An ingredient specification.

    Ingredients annotate a material with information about its usage in a process.

    Parameters
    ----------
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the ingredient spec.
    material: MaterialSpec
        Material that this ingredient is.
    process: ProcessSpec
        Process that this ingredient is used in.
    mass_fraction: :py:class:`ContinuousValue \
    <gemd.entity.value.continuous_value.ContinuousValue>`, optional
        The mass fraction of the ingredient in the process.
    volume_fraction: :py:class:`ContinuousValue \
    <gemd.entity.value.continuous_value.ContinuousValue>`, optional
        The volume fraction of the ingredient in the process.
    number_fraction: :py:class:`ContinuousValue \
    <gemd.entity.value.continuous_value.ContinuousValue>`, optional
        The number fraction of the ingredient in the process.
    absolute_quantity: :py:class:`ContinuousValue \
    <gemd.entity.value.continuous_value.ContinuousValue>`, optional
        The absolute quantity of the ingredient in the process.
    name: str
        Label on the ingredient that is unique within the process that contains it.
    labels: List[str], optional
        Additional labels on the ingredient.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDIngredientSpec.typ  # 'ingredient_spec'

    uids = Mapping(String('scope'), String('id'), 'uids', override=True)
    tags = PropertyOptional(PropertyList(String()), 'tags', override=True)
    notes = PropertyOptional(String(), 'notes', override=True)
    material = PropertyOptional(LinkOrElse(), 'material', override=True)
    process = PropertyOptional(LinkOrElse(), 'process', override=True)
    mass_fraction = PropertyOptional(Object(ContinuousValue), 'mass_fraction', override=True)
    volume_fraction = PropertyOptional(Object(ContinuousValue), 'volume_fraction', override=True)
    number_fraction = PropertyOptional(Object(ContinuousValue), 'number_fraction', override=True)
    absolute_quantity = PropertyOptional(
        Object(ContinuousValue), 'absolute_quantity', override=True)
    name = String('name', override=True)
    labels = PropertyOptional(PropertyList(String()), 'labels', override=True)
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links', override=True)
    typ = String('type')

    def __init__(self,
                 name: str,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 material: Optional[GEMDMaterialSpec] = None,
                 process: Optional[GEMDProcessSpec] = None,
                 mass_fraction: Optional[ContinuousValue] = None,
                 volume_fraction: Optional[ContinuousValue] = None,
                 number_fraction: Optional[ContinuousValue] = None,
                 absolute_quantity: Optional[ContinuousValue] = None,
                 labels: Optional[List[str]] = None,
                 file_links: Optional[List[FileLink]] = None):
        if uids is None:
            uids = dict()

        DataConcepts.__init__(self, GEMDIngredientSpec.typ)
        GEMDIngredientSpec.__init__(self, uids=uids, tags=tags, notes=notes,
                                    material=material, process=process,
                                    mass_fraction=mass_fraction, volume_fraction=volume_fraction,
                                    number_fraction=number_fraction,
                                    absolute_quantity=absolute_quantity, labels=labels,
                                    name=name, file_links=file_links)

    def __str__(self):
        return '<Ingredient spec {!r}>'.format(self.name)


class IngredientSpecCollection(ObjectSpecCollection[IngredientSpec]):
    """Represents the collection of all ingredient specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/ingredient-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/ingredient-specs'
    _individual_key = 'ingredient_spec'
    _collection_key = 'ingredient_specs'
    _resource = IngredientSpec

    @classmethod
    def get_type(cls) -> Type[IngredientSpec]:
        """Return the resource type in the collection."""
        return IngredientSpec

    def list_by_process(self,
                        uid: Union[UUID, str],
                        scope: str = CITRINE_SCOPE) -> Iterator[IngredientSpec]:
        """
        [ALPHA] Get ingredients to a process.

        Parameters
        ----------
        uid
            The unique ID of the process whose ingredients are to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[IngredientSpec]
            The ingredients to the specified process.

        """
        return self._get_relation(relation='process-specs', uid=uid, scope=scope)

    def list_by_material(self,
                         uid: Union[UUID, str],
                         scope: str = CITRINE_SCOPE) -> Iterator[IngredientSpec]:
        """
        [ALPHA] Get ingredients using the specified material.

        Parameters
        ----------
        uid
            The unique ID of the material whose ingredient usages are to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[IngredientSpec]
            The ingredients using the specified material

        """
        return self._get_relation(relation='material-specs', uid=uid, scope=scope)
