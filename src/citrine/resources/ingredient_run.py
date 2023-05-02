"""Resources that represent ingredient run data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import String, LinkOrElse, Object
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.ingredient_run import IngredientRun as GEMDIngredientRun
from gemd.entity.object.ingredient_spec import IngredientSpec as GEMDIngredientSpec
from gemd.entity.object.material_run import MaterialRun as GEMDMaterialRun
from gemd.entity.object.process_run import ProcessRun as GEMDProcessRun
from gemd.entity.value.continuous_value import ContinuousValue


class IngredientRun(
    GEMDResource['IngredientRun'],
    ObjectRun,
    GEMDIngredientRun,
    typ=GEMDIngredientRun.typ
):
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
    spec: IngredientSpec
        The specification of which this ingredient is a realization.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDIngredientRun.typ  # 'ingredient_run'

    material = PropertyOptional(LinkOrElse(GEMDMaterialRun), 'material', override=True)
    process = PropertyOptional(LinkOrElse(GEMDProcessRun),
                               'process',
                               override=True,
                               use_init=True,
                               )
    mass_fraction = PropertyOptional(Object(ContinuousValue), 'mass_fraction')
    volume_fraction = PropertyOptional(Object(ContinuousValue), 'volume_fraction')
    number_fraction = PropertyOptional(Object(ContinuousValue), 'number_fraction')
    absolute_quantity = PropertyOptional(Object(ContinuousValue), 'absolute_quantity')
    spec = PropertyOptional(LinkOrElse(GEMDIngredientSpec), 'spec', override=True, use_init=True)

    """
    Intentionally private because they have some unusual dynamics
    """
    _name = PropertyOptional(String(), 'name')
    _labels = PropertyOptional(PropertyList(String()), 'labels')

    def __init__(self,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 material: Optional[GEMDMaterialRun] = None,
                 process: Optional[GEMDProcessRun] = None,
                 mass_fraction: Optional[ContinuousValue] = None,
                 volume_fraction: Optional[ContinuousValue] = None,
                 number_fraction: Optional[ContinuousValue] = None,
                 absolute_quantity: Optional[ContinuousValue] = None,
                 spec: Optional[GEMDIngredientSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        if uids is None:
            uids = dict()
        super(ObjectRun, self).__init__()
        GEMDIngredientRun.__init__(self, uids=uids, tags=tags, notes=notes,
                                   material=material, process=process,
                                   mass_fraction=mass_fraction, volume_fraction=volume_fraction,
                                   number_fraction=number_fraction,
                                   absolute_quantity=absolute_quantity,
                                   spec=spec, file_links=file_links)

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

    def list_by_spec(self,
                     uid: Union[UUID, str, LinkByUID, GEMDIngredientSpec]
                     ) -> Iterator[IngredientRun]:
        """
        Get the ingredient runs using the specified ingredient spec.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDIngredientSpec]
            A representation of the ingredient spec whose ingredient run usages are to be located.

        Returns
        -------
        Iterator[IngredientRun]
            The ingredient runs using the specified ingredient spec.

        """
        return self._get_relation(relation='ingredient-specs', uid=uid)

    def list_by_process(self,
                        uid: Union[UUID, str, LinkByUID, GEMDProcessRun]
                        ) -> Iterator[IngredientRun]:
        """
        Get ingredients to a process.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDProcessRun]
            A representation of the process whose ingredients are to be located.

        Returns
        -------
        Iterator[IngredientRun]
            The ingredients to the specified process.

        """
        return self._get_relation(relation='process-runs', uid=uid)

    def list_by_material(self,
                         uid: Union[UUID, str, LinkByUID, GEMDMaterialRun]
                         ) -> Iterator[IngredientRun]:
        """
        Get ingredients using the specified material.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDMaterialRun]
            A representation of the material whose ingredient run usages are to be located.

        Returns
        -------
        Iterator[IngredientRun]
            The ingredients using the specified material

        """
        return self._get_relation(relation='material-runs', uid=uid)
