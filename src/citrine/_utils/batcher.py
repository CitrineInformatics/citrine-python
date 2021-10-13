from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List

from citrine.resources.data_concepts import DataConcepts

from gemd.util import writable_sort_order
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.has_parameters import HasParameters
from gemd.entity.object.has_conditions import HasConditions
from gemd.entity.object.has_properties import HasProperties
from gemd.entity.object.has_template import HasTemplate
from gemd.entity.template.has_parameter_templates import HasParameterTemplates
from gemd.entity.template.has_condition_templates import HasConditionTemplates
from gemd.entity.template.has_property_templates import HasPropertyTemplates

from gemd.entity.object import IngredientRun, MaterialRun, MeasurementRun, ProcessRun
from gemd.entity.object import IngredientSpec, MaterialSpec  # no ProcessSpec


class Batcher(ABC):
    """Base class for Data Concepts batching routines."""

    @abstractmethod
    def batch(self, objects: List[DataConcepts], batch_size) -> List[List[DataConcepts]]:
        """Collect a list of DataConcepts into batches according to some batching algorithm."""

    @staticmethod
    def by_type():
        """Return a BatchByType batcher."""
        return BatchByType()

    @staticmethod
    def by_dependency():
        """Return a BatchByDependency batcher."""
        return BatchByDependency()


class BatchByType(Batcher):
    """Batching by object type."""

    def batch(self, objects: List[DataConcepts], batch_size) -> List[List[DataConcepts]]:
        """Collect object batches by type, following an order that will satisfy prereqs."""
        batches = list()
        by_type = defaultdict(list)
        for obj in objects:
            by_type[obj.typ].append(obj)
        typ_groups = sorted(list(by_type.values()), key=lambda x: writable_sort_order(x[0]))
        for typ_group in typ_groups:
            num_batches = len(typ_group) // batch_size
            for batch_num in range(num_batches + 1):
                batch = typ_group[batch_num * batch_size: (batch_num + 1) * batch_size]
                batches.append(batch)

        return batches


class BatchByDependency(Batcher):
    """Batching by clusters where nothing references anything outside the cluster."""

    def batch(self, objects: List[DataConcepts], batch_size) -> List[List[DataConcepts]]:
        """Collect object batches that are internally consistent for dry_run object tests."""
        # Collect shallow dependences, UID references, and type-based clusters
        depends = dict()
        derefs = dict()
        by_type = defaultdict(list)
        for obj in objects:
            derefs[obj] = obj  # no-op to skip conditional later
            # Index LinkByUIDs
            for this_scope in obj.uids:
                derefs[LinkByUID.from_entity(obj, scope=this_scope)] = obj
            depends[obj] = self._all_dependencies(obj)
            by_type[obj.typ].append(obj)

        # Deep dependencies w/ objects only, build inverse index
        # This takes a second loop because we need to build up all derefs first
        supported_by = defaultdict(list)
        type_groups = sorted(list(by_type.values()), key=lambda x: writable_sort_order(x[0]))
        for type_group in type_groups:
            for obj in type_group:
                local_set = {derefs[x] for x in depends[obj] if x in derefs}
                full_set = set(local_set)
                if len(full_set) > batch_size:
                    raise ValueError(f"Object {obj.name} has more than {batch_size} dependencies.")

                for subobj in local_set:
                    full_set.update(depends[subobj])
                depends[obj] = sorted(list(full_set),
                                      key=lambda x: writable_sort_order(x))
                for dependant in reversed(depends[obj]):
                    supported_by[dependant].append(obj)

        # Build self-consistent clusters
        queued = set()
        clusters = list()
        for type_group in reversed(type_groups):  # Later objects have more dependencies
            for obj in type_group:
                if obj in queued:
                    continue  # It's already in a cluster
                to_be_checked = depends[obj]
                cluster = {obj} | set(depends[obj])
                while to_be_checked:
                    parent = to_be_checked.pop()
                    for candidate in reversed(supported_by[parent]):
                        if candidate in queued or candidate in cluster:
                            continue  # It's already in a cluster
                        candidate_set = {candidate} | set(depends[candidate])
                        if len(cluster | candidate_set) > batch_size:
                            continue  # It wouldn't fit

                        to_be_checked.extend(candidate_set - cluster)
                        cluster |= candidate_set

                clusters.append(list(cluster))
                queued.update(cluster)

        return clusters

    @staticmethod
    def _all_dependencies(obj: DataConcepts):
        """Map out all the objects that this object depends on."""
        depends = []

        # Index attribute templates from attributes
        if isinstance(obj, HasParameters):
            for attr in obj.parameters:
                if attr.template is not None:
                    depends.append(attr.template)
        if isinstance(obj, HasConditions):
            for attr in obj.conditions:
                if attr.template is not None:
                    depends.append(attr.template)
        if isinstance(obj, HasProperties):
            for attr in obj.properties:
                if attr.template is not None:
                    depends.append(attr.template)
        if isinstance(obj, MaterialSpec):
            for attr in obj.properties:
                if attr.property.template is not None:
                    depends.append(attr.property.template)
                for condition in attr.conditions:
                    if condition.template is not None:
                        depends.append(condition.template)

        # Index direct attribute template dependencies
        if isinstance(obj, HasPropertyTemplates):
            for attr in obj.properties:
                depends.append(attr[0])
        if isinstance(obj, HasConditionTemplates):
            for attr in obj.conditions:
                depends.append(attr[0])
        if isinstance(obj, HasParameterTemplates):
            for attr in obj.parameters:
                depends.append(attr[0])

        if isinstance(obj, HasTemplate):
            if obj.template is not None:
                depends.append(obj.template)
        if isinstance(obj, (IngredientRun, MaterialRun, MeasurementRun, ProcessRun)):
            if obj.spec is not None:
                depends.append(obj.spec)
        if isinstance(obj, (IngredientRun, IngredientSpec, MeasurementRun)):
            if obj.material is not None:
                depends.append(obj.material)
        if isinstance(obj, (IngredientRun, IngredientSpec, MaterialRun, MaterialSpec)):
            if obj.process is not None:
                depends.append(obj.process)

        return depends
