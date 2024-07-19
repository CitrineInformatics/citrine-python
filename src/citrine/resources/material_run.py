"""Resources that represent material run data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, LinkOrElse
from citrine._utils.functions import format_escaped_url
from citrine.resources.data_concepts import _make_link_by_uid
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_run import MaterialRun as GEMDMaterialRun
from gemd.entity.object.material_spec import MaterialSpec as GEMDMaterialSpec
from gemd.entity.template.material_template import MaterialTemplate as GEMDMaterialTemplate
from gemd.entity.object.process_run import ProcessRun as GEMDProcessRun


class MaterialRun(
    GEMDResource['MaterialRun'],
    ObjectRun,
    GEMDMaterialRun,
    typ=GEMDMaterialRun.typ
):
    """
    A material run.

    Parameters
    ----------
    name: str
        Name of the material run.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the material run.
    process: ProcessRun
        Process that produces this material.
    sample_type: str, optional
        The form of this sample. Optionals are "experimental", "virtual", "production", or
        "unknown." Default is "unknown."
    spec: MaterialSpec
        The material specification of which this is an instance.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDMaterialRun.typ  # 'material_run'

    name = String('name', override=True, use_init=True)
    process = PropertyOptional(LinkOrElse(GEMDProcessRun),
                               'process',
                               override=True,
                               use_init=True,)
    sample_type = PropertyOptional(String, 'sample_type', override=True)
    spec = PropertyOptional(LinkOrElse(GEMDMaterialSpec),
                            'spec',
                            override=True,
                            use_init=True,)

    def __init__(self,
                 name: str,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 process: Optional[GEMDProcessRun] = None,
                 sample_type: Optional[str] = "unknown",
                 spec: Optional[GEMDMaterialSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        if uids is None:
            uids = dict()
        super(ObjectRun, self).__init__()
        GEMDMaterialRun.__init__(self, name=name, uids=uids,
                                 tags=tags, process=process,
                                 sample_type=sample_type, spec=spec,
                                 file_links=file_links, notes=notes)

    def __str__(self):
        return '<Material run {!r}>'.format(self.name)


class MaterialRunCollection(ObjectRunCollection[MaterialRun]):
    """Represents the collection of all material runs associated with a dataset."""

    _individual_key = 'material_run'
    _collection_key = 'material_runs'
    _resource = MaterialRun

    @classmethod
    def get_type(cls) -> Type[MaterialRun]:
        """Return the resource type in the collection."""
        return MaterialRun

    def get_history(self, id: Union[str, UUID, LinkByUID, MaterialRun]) -> MaterialRun:
        """
        Get the history associated with a terminal material.

        The history contains every single every process, ingredient and material that went into
        the terminal material as well as the measurements that were performed on all of those
        materials. The returned object is a material run with all of its fields fully populated.

        Parameters
        ----------
        id: Union[UUID, str, LinkByUID, MaterialRun]
            A representation of the material whose history is to be retrieved

        Returns
        -------
        MaterialRun
            A material run that has all of its fields fully populated with the processes,
            ingredients, measurements, and other materials that were involved in the history
            of the object.

        """
        link = _make_link_by_uid(id)
        path = format_escaped_url(
            "teams/{}/gemd/query/material-histories?filter_nonroot_materials=true",
            self.team_id)
        query = {
            "criteria": [
                {
                    "datasets": [str(self.dataset_id)],
                    "type": "terminal_material_run_identifiers_criteria",
                    "terminal_material_ids": [
                        {
                            "scope": link.scope,
                            "id": link.id
                        }
                    ]
                }
            ]
        }
        data = self.session.post_resource(path, json=query)
        if data and data[0].get("roots"):
            # Since the above query presents a single dataset to the endpoint, the response will be
            # a list of length one, with a single route.
            # Note that "object" is used to match gemd-python expectations, although that library
            # can handle different names.
            history_data = data[0]
            history_data["object"] = history_data.pop("roots")[0]
            return MaterialRun.build(history_data)
        else:
            return None

    def get_by_process(self,
                       uid: Union[UUID, str, LinkByUID, GEMDProcessRun]
                       ) -> Optional[MaterialRun]:
        """
        Get output material of a process.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDProcessRun]
            A representation of the process whose output is to be located.

        Returns
        -------
        MaterialRun
            The output material of the specified process, or None if no such material exists.

        """
        return next(
            self._get_relation(relation='process-runs', uid=uid, per_page=1),
            None
        )

    def list_by_spec(self,
                     uid: Union[UUID, str, LinkByUID, GEMDMaterialSpec]
                     ) -> Iterator[MaterialRun]:
        """
        Get the material runs using the specified material spec.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDMaterialSpec]
            A representation of the material spec whose material run usages are to be located.

        Returns
        -------
        Iterator[MaterialRun]
            The material runs using the specified material spec.

        """
        return self._get_relation('material-specs', uid=uid)

    def list_by_template(self,
                         uid: Union[UUID, str, LinkByUID, GEMDMaterialTemplate]
                         ) -> Iterator[MaterialRun]:
        """
        Get the material runs using the specified material template.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDMaterialTemplate]
            A representation of the material template whose material run usages are to be located.

        Returns
        -------
        Iterator[MaterialRun]
            The material runs using the specified material template.

        """
        spec_collection = MaterialSpecCollection(
            team_id=self.team_id,
            dataset_id=self.dataset_id,
            session=self.session
        )
        specs = spec_collection.list_by_template(uid=_make_link_by_uid(uid))
        return (run for runs in (self.list_by_spec(spec) for spec in specs)
                for run in runs)
