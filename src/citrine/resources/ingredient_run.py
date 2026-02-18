"""Resources that represent ingredient run data objects."""
from collections.abc import Iterator
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import LinkOrElse, List, Object, Optional, String
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
    tags: list[str], optional
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
    file_links: list[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDIngredientRun.typ  # 'ingredient_run'

    material = Optional(LinkOrElse(GEMDMaterialRun), 'material', override=True)
    process = Optional(LinkOrElse(GEMDProcessRun), 'process', override=True, use_init=True)
    mass_fraction = Optional(Object(ContinuousValue), 'mass_fraction')
    volume_fraction = Optional(Object(ContinuousValue), 'volume_fraction')
    number_fraction = Optional(Object(ContinuousValue), 'number_fraction')
    absolute_quantity = Optional(Object(ContinuousValue), 'absolute_quantity')
    spec = Optional(LinkOrElse(GEMDIngredientSpec), 'spec', override=True, use_init=True)

    """
    Intentionally private because they have some unusual dynamics
    """
    _name = Optional(String(), 'name')
    _labels = Optional(List(String()), 'labels')

    def __init__(self,
                 *,
                 uids: dict[str, str] | None = None,
                 tags: list[str] | None = None,
                 notes: str | None = None,
                 material: GEMDMaterialRun | None = None,
                 process: GEMDProcessRun | None = None,
                 mass_fraction: ContinuousValue | None = None,
                 volume_fraction: ContinuousValue | None = None,
                 number_fraction: ContinuousValue | None = None,
                 absolute_quantity: ContinuousValue | None = None,
                 spec: GEMDIngredientSpec | None = None,
                 file_links: list[FileLink] | None = None):
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

    _individual_key = 'ingredient_run'
    _collection_key = 'ingredient_runs'
    _resource = IngredientRun

    @classmethod
    def get_type(cls) -> type[IngredientRun]:
        """Return the resource type in the collection."""
        return IngredientRun

    def list_by_spec(self,
                     uid: UUID | str | LinkByUID | GEMDIngredientSpec
                     ) -> Iterator[IngredientRun]:
        """
        Get the ingredient runs using the specified ingredient spec.

        Parameters
        ----------
        uid: UUID | str | LinkByUID | GEMDIngredientSpec
            A representation of the ingredient spec whose ingredient run usages are to be located.

        Returns
        -------
        Iterator[IngredientRun]
            The ingredient runs using the specified ingredient spec.

        """
        return self._get_relation(relation='ingredient-specs', uid=uid)

    def list_by_process(self,
                        uid: UUID | str | LinkByUID | GEMDProcessRun
                        ) -> Iterator[IngredientRun]:
        """
        Get ingredients to a process.

        Parameters
        ----------
        uid: UUID | str | LinkByUID | GEMDProcessRun
            A representation of the process whose ingredients are to be located.

        Returns
        -------
        Iterator[IngredientRun]
            The ingredients to the specified process.

        """
        return self._get_relation(relation='process-runs', uid=uid)

    def list_by_material(self,
                         uid: UUID | str | LinkByUID | GEMDMaterialRun
                         ) -> Iterator[IngredientRun]:
        """
        Get ingredients using the specified material.

        Parameters
        ----------
        uid: UUID | str | LinkByUID | GEMDMaterialRun
            A representation of the material whose ingredient run usages are to be located.

        Returns
        -------
        Iterator[IngredientRun]
            The ingredients using the specified material

        """
        return self._get_relation(relation='material-runs', uid=uid)
