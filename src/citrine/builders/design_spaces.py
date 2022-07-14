import csv
from logging import getLogger
from uuid import UUID

from citrine.exceptions import BadRequest
from citrine.informatics.data_sources import CSVDataSource
from citrine.resources.dataset import Dataset
from citrine.resources.project import Project

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    raise ImportError('pandas>=1.1.5 is a requirement for the builders module')
try:
    import numpy as np
except ImportError:  # pragma: no cover
    raise ImportError('numpy is a requirement for the builders module')
from itertools import product
from typing import Mapping, Sequence, List, Optional
from citrine.informatics.design_spaces import EnumeratedDesignSpace, DataSourceDesignSpace
from citrine.informatics.descriptors import Descriptor, RealDescriptor

logger = getLogger(__name__)


def enumerate_cartesian_product(
    *,
    design_grid: Mapping[str, Sequence],
    descriptors: List[Descriptor],
    name: str,
    description: str = ''
) -> EnumeratedDesignSpace:
    """[ALPHA] Enumerate a Cartesian product from 1-D grids.

    Given a dict of lists or tuples of values for each design descriptor,
    create the list of candidates representing the Cartesian product of all
    values for each descriptor

    Parameters
    ----------
    design_grid: Mapping[str, Sequence]
        {'descriptor key': [sequence, of, values]} for each descriptor
    descriptors: List[Descriptor]
        design descriptors representing the degrees of freedom of the design
        space. descriptors' keys should match the keys of design_grid. If
        none are passed, they will be auto-generated based on the keys
        of design_grid.
    name: str
        name for the EnumeratedDesignSpace
    description: str
        description for the EnumeratedDesignSpace

    """
    # Check that the grid size is small enough to not cause memory issues
    grid_size = np.prod(
        [len(grid_points) for grid_points in design_grid.values()]
    ) * len(design_grid)
    if grid_size > 2E8:
        logger.warning(
            "Product design grid contains {n} grid points. This may cause memory issues "
            "downstream.".format(n=grid_size)
        )

    design_space_tuples = list(product(*design_grid.values()))
    design_space_cols = list(design_grid.keys())
    df_ds = pd.DataFrame(data=design_space_tuples, columns=design_space_cols)
    data = df_ds.to_dict('records')
    design_space = EnumeratedDesignSpace(name=name,
                                         description=description,
                                         descriptors=descriptors,
                                         data=data)
    return design_space


def enumerate_formulation_grid(
    *,
    formulation_grid: Mapping[str, Sequence[float]],
    balance_ingredient: str,
    descriptors: List[Descriptor] = None,
    name: str,
    description: str = ''
) -> EnumeratedDesignSpace:
    """[ALPHA] Enumerate a Cartesian product following formulation constraints.

    Given a dict of grids (lists) of ingredient amounts (fractions, between
    0-1), create candidates that are the Cartesian product of all possible
    formulations with combinations of the specified ingredient amounts.
    The balance_ingredient will make up the balance of the formulation. In
    other words, this function first takes the Cartesian product of all
    ingredient amounts *except* the balance_ingredient, then fills in the
    amount of balance_ingredient as 1-(other ingredients). Results for which
    the balance ingredient falls outside of the min and max values in its list
    will be filtered out. Because of this, not all values in the balance
    ingredient's list will necessarily be present in the final candidates.

    For example:

    {'balance ingredient':[0.8, 0.85, 0.9],
     'other ingredient':[0.1, 0.2, 0.3, 0.4, 0.5]}

    would yield:

    [{'balance ingredient': 0.8, 'other ingredient': 0.2},
     {'balance ingredient': 0.9, 'other ingredient': 0.1}]

    Parameters
    ----------
    formulation_grid: Mapping[str, Sequence]
        {'ingredient name':[list, of, values]} for each ingredient
    balance_ingredient: str
        name of the ingredient that should make up the balance of the
        mixture (1-others). Must be a key in formulation_grid.
    descriptors: List[Descriptor]
        design descriptors representing the degrees of freedom of the design
        space. descriptors' keys should match the keys of formulation_grid.
        If none are passed, they will be auto-generated based on the keys
        of formulation_grid.
    name: str
        name for the EnumeratedDesignSpace
    description: str
        description for the EnumeratedDesignSpace

    """
    # Generate descriptors if none passed
    if descriptors is None:
        descriptors = [RealDescriptor(kk, lower_bound=0, upper_bound=1, units="")
                       for kk in formulation_grid.keys()]

    # Check that the passed balance ingredient is in the grid keys
    if balance_ingredient not in list(formulation_grid.keys()):
        raise ValueError("balance_ingredient must be in formulation_grid' keys")

    # Check that all grid values are between 0 and 1
    for kk, val_list in formulation_grid.items():
        if not (all([x >= 0 for x in val_list]) and all([x <= 1 for x in val_list])):
            raise ValueError('values in {} are not between 0 and 1'.format(kk))

    non_balance_ingrs = [ingr for ingr in list(formulation_grid.keys())
                         if ingr != balance_ingredient]
    non_balance_descriptors = [dd for dd in descriptors
                               if dd.key != balance_ingredient]
    non_balance_grids = {
        k: v for k, v in formulation_grid.items()
        if k in non_balance_ingrs
    }

    # Start by making a naive product design space of non-balance ingredients
    form_ds = pd.DataFrame(
        enumerate_cartesian_product(
            design_grid=non_balance_grids,
            descriptors=non_balance_descriptors,
            name='',
            description=''
        ).data
    )

    # Re-calculate the balance ingredient column as 1-all others
    form_ds[balance_ingredient] = form_ds.apply(
        lambda r: 1 - sum([r[col] for col in non_balance_ingrs]),
        axis=1
    )

    # Order columns so balance ingredient is first
    form_ds = form_ds[[balance_ingredient] + non_balance_ingrs]

    # Eliminate out-of-range rows
    balance_range = (
        min(formulation_grid[balance_ingredient]),
        max(formulation_grid[balance_ingredient])
    )
    form_ds = form_ds[form_ds[balance_ingredient] >= balance_range[0]]
    form_ds = form_ds[form_ds[balance_ingredient] <= balance_range[1]]
    data = form_ds.to_dict('records')
    design_space = EnumeratedDesignSpace(name=name,
                                         description=description,
                                         descriptors=descriptors,
                                         data=data)
    return design_space


def cartesian_join_design_spaces(
    *,
    subspaces: List[EnumeratedDesignSpace],
    name: str,
    description: str = ''
) -> EnumeratedDesignSpace:
    """[ALPHA] Cartesian join of multiple enumerated design spaces.

    Given a list of multiple input EnumeratedDesignSpaces, create a new
    EnumeratedDesignSpace that is the Cartesian product of candidates from each
    input design space.

    Ultimate length will be the product of the number of candidates in each
    individual design space

    Parameters
    ----------
    subspaces: List[EnumeratedDesignSpace]
        A list of EnumeratedDesignSpaces
    name: str
        name for the output EnumeratedDesignSpace
    description: str
        description for the output EnumeratedDesignSpace

    """
    # Test for duplicate or invalid descriptor keys
    all_keys = []
    for ds in subspaces:
        if 'join_key' in ds.data[0].keys():
            raise ValueError('"join_key" cannot be a descriptor key when using this function')
        all_keys.extend(list(ds.data[0].keys()))
    if len(all_keys) != len(set(all_keys)):
        raise ValueError('Duplicate keys are not allowed across design spaces')

    # Check that the grid size is small enough to not cause memory issues
    grid_size = np.prod([len(ds.data) for ds in subspaces]) \
        * np.sum([len(ds.data[0]) for ds in subspaces])
    if grid_size > 2E8:
        logger.warning(
            "Product design grid contains {n} grid points. This may cause memory issues "
            "downstream.".format(n=grid_size)
        )

    # Convert data fields of EDS into DataFrames to prep for join
    ds_list = [pd.DataFrame(ds.data) for ds in subspaces]

    # Set a dummy column to do the join
    for df in ds_list:
        df['join_key'] = 0

    # Perform the join
    df_join = ds_list[0]
    for df in ds_list[1:]:
        df_join = pd.merge(df_join, df, on='join_key')

    # Drop the dummy column and convert back to List[dict]
    df_join = df_join.drop(columns='join_key')
    data = df_join.to_dict('records')

    # Build the final DesignSpace
    descriptors = []
    for ds in subspaces:
        descriptors.extend(ds.descriptors)
    design_space = EnumeratedDesignSpace(name=name,
                                         description=description,
                                         descriptors=descriptors,
                                         data=data)
    return design_space


def enumerated_to_data_source(*,
                              enumerated_ds: EnumeratedDesignSpace,
                              dataset: Dataset,
                              filename: Optional[str] = None
                              ) -> DataSourceDesignSpace:
    """[ALPHA] Convert an EnumeratedDesignSpace into a DataSourceDesignSpace.

    Converts an EnumeratedDesignSpace into a DataSourceDesignSpace by writing
    the data to a csv file, uploading it to the given dataset, and wrapping it
    in a CSVDataSource.

    Parameters
    ----------
    enumerated_ds: EnumeratedDesignSpace
        data source to convert
    dataset: Dataset
        dataset into which to upload the data file
    filename: Optional[str]
        filename to use for the data file (default: design space name + "source data")

    """
    descriptors = {d.key: d for d in enumerated_ds.descriptors}
    headers = [d.key for d in enumerated_ds.descriptors]

    csv_filename = filename or "{} source data.csv".format(enumerated_ds.name).replace(" ", "_")
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for datum in enumerated_ds.data:
            writer.writerow([datum.get(k, '') for k in headers])

    file_link = dataset.files.upload(csv_filename)
    data_source = CSVDataSource(file_link=file_link, column_definitions=descriptors)
    data_source_ds = DataSourceDesignSpace(
        name=enumerated_ds.name, description=enumerated_ds.description, data_source=data_source)
    return data_source_ds


def migrate_enumerated_design_space(*,
                                    project: Project,
                                    uid: UUID,
                                    dataset: Dataset,
                                    filename: Optional[str],
                                    cleanup: bool = True
                                    ) -> DataSourceDesignSpace:
    """
    [ALPHA] Migrate an EnumeratedDesignSpace on the Citrine Platform to a DataSourceDesignSpace.

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform
    uid: UUID
        Unique identifier of the EnumeratedDesignSpace to migrate
    dataset: Dataset
        Dataset into which to write the data as a CSV.
    filename: Optional[str]
        Optional string name to specify for the data CSV file.
        Defaults to the design space name + "source data"
    cleanup: bool
        Whether or not to try and archive the migrated design space if the migration is successful
        Default: true

    Returns
    -------
    DataSourceDesignSpace
        The resulting design space, which should have functional parity with
        the original design space.

    """
    enumerated_ds = project.design_spaces.get(uid)
    if not isinstance(enumerated_ds, EnumeratedDesignSpace):
        msg = "Trying to migrate an enumerated design space but this is a {}".format(
            type(enumerated_ds))
        raise ValueError(msg)

    # create the new data source design space
    data_source_ds = enumerated_to_data_source(
        enumerated_ds=enumerated_ds, dataset=dataset, filename=filename)
    data_source_ds = project.design_spaces.register(data_source_ds)

    if cleanup:
        # archive the old enumerated design space
        try:
            project.design_spaces.archive(enumerated_ds.uid)
        except BadRequest as err:
            logger.warning(f"Unable to archive design space with uid {uid}, "
                           f"received the following response: {err.response_text}")

    return data_source_ds
