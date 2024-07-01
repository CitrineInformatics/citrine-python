"""Resources that represent process run data objects."""
from typing import List, Dict, Optional, Type, Union, Iterator
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Object, LinkOrElse
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.process_run import ProcessRun as GEMDProcessRun
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.source.performed_source import PerformedSource


class ProcessRun(GEMDResource['ProcessRun'], ObjectRun, GEMDProcessRun, typ=GEMDProcessRun.typ):
    """
    A process run.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process run.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the process run.
    conditions: List[Condition], optional
        Conditions under which this process run occurs.
    parameters: List[Parameter], optional
        Parameters of this process run.
    spec: ProcessSpec
        Spec for this process run.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.
    source: PerformedSource, optional
        Information about the person who performed the run and when.

    """

    _response_key = GEMDProcessRun.typ  # 'process_run'

    name = String('name', override=True, use_init=True)
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions', override=True)
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters', override=True)
    spec = PropertyOptional(LinkOrElse(GEMDProcessSpec), 'spec', override=True, use_init=True,)
    source = PropertyOptional(Object(PerformedSource), "source", override=True)

    def __init__(self,
                 name: str,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 spec: Optional[GEMDProcessSpec] = None,
                 file_links: Optional[List[FileLink]] = None,
                 source: Optional[PerformedSource] = None):
        if uids is None:
            uids = dict()
        super(ObjectRun, self).__init__()
        GEMDProcessRun.__init__(self, name=name, uids=uids,
                                tags=tags, conditions=conditions, parameters=parameters,
                                spec=spec, file_links=file_links, notes=notes, source=source)

    def __str__(self):
        return '<Process run {!r}>'.format(self.name)


class ProcessRunCollection(ObjectRunCollection[ProcessRun]):
    """Represents the collection of all process runs associated with a dataset."""

    _individual_key = 'process_run'
    _collection_key = 'process_runs'
    _resource = ProcessRun

    @classmethod
    def get_type(cls) -> Type[ProcessRun]:
        """Return the resource type in the collection."""
        return ProcessRun

    def list_by_spec(self,
                     uid: Union[UUID, str, LinkByUID, GEMDProcessSpec]
                     ) -> Iterator[ProcessRun]:
        """
        Get the process runs using the specified process spec.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDProcessSpec]
            A representation of the process spec whose process run usages are to be located.

        Returns
        -------
        Iterator[ProcessRun]
            The process runs using the specified process spec.

        """
        return self._get_relation('process-specs', uid=uid)
