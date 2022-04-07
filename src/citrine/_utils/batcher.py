from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Iterable

from citrine.resources.data_concepts import DataConcepts

from gemd.util import make_index, writable_sort_order


class Batcher(ABC):
    """Base class for Data Concepts batching routines."""

    @abstractmethod
    def batch(self, objects: Iterable[DataConcepts], batch_size) -> List[List[DataConcepts]]:
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

    def batch(self, objects: Iterable[DataConcepts], batch_size) -> List[List[DataConcepts]]:
        """Collect object batches by type, following an order that will satisfy prereqs."""
        batches = list()
        by_type = defaultdict(list)
        seen = {}
        for obj in objects:
            if obj.to_link() in seen:  # Repeat in the iterable; don't add it to the batch
                if seen[obj.to_link()] != obj:  # verify that it's a replicate
                    raise ValueError(f"Colliding objects for {obj.to_link()}")
            else:
                by_type[obj.typ].append(obj)
                for scope in obj.uids:
                    seen[obj.to_link(scope)] = obj
        typ_groups = sorted(list(by_type.values()), key=lambda x: writable_sort_order(x[0]))
        for typ_group in typ_groups:
            num_batches = len(typ_group) // batch_size
            for batch_num in range(num_batches + 1):
                batch = typ_group[batch_num * batch_size: (batch_num + 1) * batch_size]
                batches.append(batch)
        for i in reversed(range(len(batches) - 1)):
            if len(batches[i]) + len(batches[i + 1]) <= batch_size:
                batches[i].extend(batches[i + 1])
                del batches[i + 1]

        return batches


class BatchByDependency(Batcher):
    """Batching by clusters where nothing references anything outside the cluster."""

    def batch(self, objects: Iterable[DataConcepts], batch_size) -> List[List[DataConcepts]]:
        """Collect object batches that are internally consistent for dry_run object tests."""
        # Collect shallow dependences, UID references, and type-based clusters
        depends = dict()
        obj_set = set(objects)
        index = make_index(objects)
        by_type = defaultdict(list)
        for obj in objects:  # Don't worry about replicates since we'd have them anyway
            depends[obj] = obj.all_dependencies()
            by_type[obj.typ].append(obj)

        # Deep dependencies w/ objects only, build inverse index
        # This takes a second loop because we need to build up all derefs first
        supported_by = defaultdict(list)
        type_groups = sorted(list(by_type.values()), key=lambda x: writable_sort_order(x[0]))
        for type_group in type_groups:
            for obj in type_group:
                # Collect objects of interest that we are supposed to load
                # Note depends contains both objects & links; obj_set is everything in the call
                local_set = {index.get(x, x) for x in depends[obj] if index.get(x, x) in obj_set}
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
