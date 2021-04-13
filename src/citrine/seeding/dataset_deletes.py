"""Functions that perform dataset deletes."""
from typing import List, Tuple

from citrine.resources.api_error import ApiError
from citrine.resources.dataset import Dataset

from gemd.entity.link_by_uid import LinkByUID


def wipe_dataset(dataset: Dataset, *, delete_templates: bool = False) -> \
        List[Tuple[LinkByUID, ApiError]]:
    """
    Wipes the GEMD objects from a dataset.

    Parameters
    ----------
    dataset : Dataset
        The dataset to remove GEMD objects from
    delete_templates : bool, optional
        An option to also remove templates from the given dataset, by default False

    Returns
    -------
    List[Tuple[LinkByUID, ApiError]]
        A list of (LinkByUID, api_error) for each failure to delete an object.
        Note that this method doesn't raise an exception if an object fails to be
        deleted.

    """
    print("Collecting GEMDs...")
    gemds = [
        *dataset.ingredient_runs.list_all(),
        *dataset.ingredient_specs.list_all(),
        *dataset.material_runs.list_all(),
        *dataset.material_specs.list_all(),
        *dataset.measurement_runs.list_all(),
        *dataset.measurement_specs.list_all(),
        *dataset.process_runs.list_all(),
        *dataset.process_specs.list_all(),
    ]
    if delete_templates:
        gemds += [
            *dataset.material_templates.list_all(),
            *dataset.measurement_templates.list_all(),
            *dataset.process_templates.list_all(),
            *dataset.property_templates.list_all(),
            *dataset.condition_templates.list_all(),
            *dataset.parameter_templates.list_all(),
        ]
    print("Deleting GEMDs...")
    del_response = dataset.gemd_batch_delete(gemds)
    return del_response
