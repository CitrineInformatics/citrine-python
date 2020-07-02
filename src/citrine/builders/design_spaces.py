try:
    import pandas as pd
except ImportError:  # pragma: no cover
    raise ImportError('pandas>=0.25 is a requirement for the builders module')
from itertools import product
from typing import Mapping, Sequence, List
from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.informatics.descriptors import Descriptor, RealDescriptor


def enumerate_cartesian_product(
    design_grids: Mapping[str, Sequence],
    descriptors: List[Descriptor],
    name: str = 'Enumerated Cartesian product design space',
    description: str = '',
) -> EnumeratedDesignSpace:
    """[ALPHA] Enumerate a Cartesian product from 1-D grids.

    Given a dict of lists or tuples of values for each design descriptor,
    create the list of candidates representing the Cartesian product of all
    values for each descriptor

    Parameters
    ----------
    design_grids: Mapping[str, Sequence]
        {'descriptor key': [sequence, of, values]} for each descriptor
    descriptors: List[Descriptor]
        design descriptors representing the degrees of freedom of the design
        space. descriptors' keys should match the keys of design_grids. If
        none are passed, they will be auto-generated based on the keys
        of design_grids.
    name: str
        name for the EnumeratedDesignSpace
    description: str
        description for the EnumeratedDesignSpace

    """
    design_space_tuples = list(product(*design_grids.values()))
    design_space_cols = list(design_grids.keys())
    df_ds = pd.DataFrame(data=design_space_tuples, columns=design_space_cols)
    data = df_ds.to_dict('records')
    design_space = EnumeratedDesignSpace(name=name,
                                         description=description,
                                         descriptors=descriptors,
                                         data=data)
    return design_space


def enumerate_formulation_grid(
    formulation_grids: Mapping[str, Sequence[float]],
    balance_component: str,
    descriptors: List[Descriptor] = None,
    name: str = 'Enumerated Formulation Grid',
    description: str = '',
) -> EnumeratedDesignSpace:
    """[ALPHA] Enumerate a Cartesian product following formulation constraints.

    Given a dict of grids (lists) of ingredient amounts (fractions, between
    0-1), create candidates that are the Cartesian product of all possible
    formulations with combinations of the specified ingredient amounts.
    The balance_component will make up the balance of the formulation. In
    other words, this function first takes the Cartesian product of all
    ingredient amounts *except* the balance_component, then fills in the
    amount of balance_component as 1-(other ingredients). Results for which
    the balance component falls outside of the min and max values in its list
    will be filtered out. Because of this, not all values in the balance
    component's list will necessarily be present in the final candidates.

    For example:

    {'balance component':[0.8, 0.85, 0.9],
     'other component':[0.1, 0.2, 0.3, 0.4, 0.5]}

    would yield:

    [{'balance component': 0.8, 'other component': 0.2},
     {'balance component': 0.9, 'other component': 0.1}]

    Parameters
    ----------
    formulation_grids: Mapping[str, Sequence]
        {'component name':[list, of, values]} for each component
    balance_component: str
        name of the component that should make up the balance of the
        mixture (1-others). Must be a key in formulation_grids.
    descriptors: List[Descriptor]
        design descriptors representing the degrees of freedom of the design
        space. descriptors' keys should match the keys of formulation_grids.
        If none are passed, they will be auto-generated based on the keys
        of formulation_grids.
    name: str
        name for the EnumeratedDesignSpace
    description: str
        description for the EnumeratedDesignSpace

    """
    # Generate descriptors if none passed
    if descriptors is None:
        descriptors = [RealDescriptor(kk, 0, 1) for kk in formulation_grids.keys()]

    # Check that the passed balance component is in the grid keys
    if balance_component not in list(formulation_grids.keys()):
        raise ValueError("balance_component must be in formulation_grids' keys")

    # Check that all grid values are between 0 and 1
    for kk, val_list in formulation_grids.items():
        if not (all([x >= 0 for x in val_list]) and all([x <= 1 for x in val_list])):
            raise ValueError('values in {} are not between 0 and 1'.format(kk))

    non_balance_comps = [comp for comp in list(formulation_grids.keys())
                         if comp != balance_component]
    non_balance_descriptors = [dd for dd in descriptors
                               if dd.key != balance_component]
    non_balance_grids = {
        k: v for k, v in formulation_grids.items()
        if k in non_balance_comps
    }

    # Start by making a naive product design space of non-balance components
    form_ds = pd.DataFrame(
        enumerate_cartesian_product(
            design_grids=non_balance_grids,
            descriptors=non_balance_descriptors
        ).data
    )

    # Re-calculate the balance component column as 1-all others
    form_ds[balance_component] = form_ds.apply(
        lambda r: 1 - sum([r[col] for col in non_balance_comps]),
        axis=1
    )

    # Order columns so balance component is first
    form_ds = form_ds[[balance_component] + non_balance_comps]

    # Eliminate out-of-range rows
    balance_range = (
        min(formulation_grids[balance_component]),
        max(formulation_grids[balance_component])
    )
    form_ds = form_ds[form_ds[balance_component] >= balance_range[0]]
    form_ds = form_ds[form_ds[balance_component] <= balance_range[1]]
    data = form_ds.to_dict('records')
    design_space = EnumeratedDesignSpace(name=name,
                                         description=description,
                                         descriptors=descriptors,
                                         data=data)
    return design_space


def cartesian_join_design_spaces(
    design_space_list: List[EnumeratedDesignSpace],
    name: str = 'Joined enumerated design space',
    description: str = '',
) -> EnumeratedDesignSpace:
    """[ALPHA] Cartesian join of multiple enumerated design spaces.

    Given a list of multiple input EnumeratedDesignSpaces, create a new
    EnumeratedDesignSpace that is the Cartesian product of candidates from each
    input design space.

    Ultimate length will be the product of the number of candidates in each
    individual design space

    Parameters
    ----------
    design_space_list: List[EnumeratedDesignSpace]
        A list of EnumeratedDesignSpaces

    """
    # Test for duplicate or invalid descriptor keys
    all_keys = []
    for ds in design_space_list:
        if 'join_key' in ds.data[0].keys():
            raise ValueError('"join_key" cannot be a descriptor key when using this function')
        all_keys.extend(list(ds.data[0].keys()))
    if len(all_keys) != len(set(all_keys)):
        raise ValueError('Duplicate keys are not allowed across design spaces')

    # Convert data fields of EDS into DataFrames to prep for join
    data_list = [ds.data for ds in design_space_list]
    ds_list = [pd.DataFrame(data) for data in data_list]

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
    for ds in design_space_list:
        descriptors.extend(ds.descriptors)
    design_space = EnumeratedDesignSpace(name=name,
                                         description=description,
                                         descriptors=descriptors,
                                         data=data)
    return design_space
