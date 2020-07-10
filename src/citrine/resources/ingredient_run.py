"""Resources that represent ingredient run data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Mapping, String, LinkOrElse, Object
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.file_link import FileLink
from gemd.entity.object.ingredient_run import IngredientRun as GEMDIngredientRun
from gemd.entity.object.ingredient_spec import IngredientSpec as GEMDIngredientSpec
from gemd.entity.object.material_run import MaterialRun as GEMDMaterialRun
from gemd.entity.object.process_run import ProcessRun as GEMDProcessRun
from gemd.entity.value.continuous_value import ContinuousValue


class IngredientRun(ObjectRun, Resource['IngredientRun'], GEMDIngredientRun):
    """
    An ingredient run.

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
        Long-form notes about the ingredient run.
    material: MaterialRun
        Material that this ingredient is.
    process: ProcessRun
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
    name: str, optional
        Label on the ingredient that is unique within the process that contains it. This property
        will be overwritten by its value in `spec` if it is present.
    labels: List[str], optional
        Additional labels on the ingredient. This property will be overwritten by its value in
        `spec` if it is present.
    spec: IngredientSpec
        The specification of which this ingredient is a realization.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDIngredientRun.typ  # 'ingredient_run'

    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    material = PropertyOptional(LinkOrElse(), 'material')
    process = PropertyOptional(LinkOrElse(), 'process')
    mass_fraction = PropertyOptional(Object(ContinuousValue), 'mass_fraction')
    volume_fraction = PropertyOptional(Object(ContinuousValue), 'volume_fraction')
    number_fraction = PropertyOptional(Object(ContinuousValue), 'number_fraction')
    absolute_quantity = PropertyOptional(
        Object(ContinuousValue), 'absolute_quantity')
    name = PropertyOptional(String(), 'name')
    labels = PropertyOptional(PropertyList(String()), 'labels')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: Optional[str] = None,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 material: Optional[GEMDMaterialRun] = None,
                 process: Optional[GEMDProcessRun] = None,
                 mass_fraction: Optional[ContinuousValue] = None,
                 volume_fraction: Optional[ContinuousValue] = None,
                 number_fraction: Optional[ContinuousValue] = None,
                 absolute_quantity: Optional[ContinuousValue] = None,
                 labels: Optional[List[str]] = None,
                 spec: Optional[GEMDIngredientSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDIngredientRun.typ)
        GEMDIngredientRun.__init__(self, uids=uids, tags=tags, notes=notes,
                                   material=material, process=process,
                                   mass_fraction=mass_fraction, volume_fraction=volume_fraction,
                                   number_fraction=number_fraction,
                                   absolute_quantity=absolute_quantity, labels=labels,
                                   name=name, spec=spec, file_links=file_links)

    def __str__(self):
        return '<Ingredient run {!r}>'.format(self.name)


class IngredientRunCollection(ObjectRunCollection[IngredientRun]):
    """Represents the collection of all ingredient runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/ingredient-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/ingredient-runs'
    _individual_key = 'ingredient_run'
    _collection_key = 'ingredient_runs'
    _resource = IngredientRun

    @classmethod
    def get_type(cls) -> Type[IngredientRun]:
        """Return the resource type in the collection."""
        return IngredientRun

    def list_by_spec(self, uid: Union[UUID, str], scope: str = 'id') -> Iterator[IngredientRun]:
        """
        [ALPHA] Get the ingredient runs using the specified ingredient spec.

        Parameters
        ----------
        uid
            The unique ID of the ingredient spec whose ingredient run usages are to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[IngredientRun]
            The ingredient runs using the specified ingredient spec.

        """
        return self._get_relation('ingredient-specs', uid=uid, scope=scope)

    def list_by_process(self, uid: Union[UUID, str], scope: str = 'id') -> Iterator[IngredientRun]:
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
        Iterator[IngredientRun]
            The ingredients to the specified process.

        """
        return self._get_relation(relation='process-runs', uid=uid, scope=scope)

    def list_by_material(self, uid: Union[UUID, str],
                         scope: str = 'id') -> Iterator[IngredientRun]:
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
        Iterator[IngredientRun]
            The ingredients using the specified material

        """
        return self._get_relation(relation='material-runs', uid=uid, scope=scope)
