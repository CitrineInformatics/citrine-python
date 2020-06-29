import pandas as pd
from itertools import product
from typing import Mapping, Sequence, List
from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.informatics.descriptors import Descriptor


def enumerate_cartesian_product(
    design_grids: Mapping[str, Sequence],
    descriptors: List[Descriptor],
    name: str = 'Enumerated Cartesian product design space',
    description: str = '',
) -> EnumeratedDesignSpace:
    """[ALPHA] Given a dict of lists or tuples of values for each design descriptor,
    create the list of candidates representing the Cartesian product of all
    values for each descriptor

    Parameters
    ----------
    design_grids: Mapping[str, Sequence]
        {'descriptor key': [sequence, of, values]} for each descriptor
    descriptors: List[Descriptor]
        design descriptors representing the degrees of freedom of the design
        space. descriptors' keys should match the keys of design_grids
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


def enumerate_simple_mixture_cartesian_product(
    formulation_grids: Mapping[str, Sequence[float]],
    balance_component: str,
    descriptors: List[Descriptor],
    name: str = 'Enumerated Cartesian product simple mixture design space',
    description: str = '',
) -> EnumeratedDesignSpace:
    """[ALPHA] Given a dict of lists or tuples of ingredient amounts (must be
    fractions of some kind, i.e. between 0-1), create candidates that are
    the Cartesian product of all possible combinations of ingredients *except*
    for the balance_component. The balance_component will then be filled in
    as 1-(all other ingredients) for each row.
    
    The balance component's [list, of, values] can be similar to the other
    components'; in this way, the balance component can be swapped out easily.
    However, the balance component's intermediate values will be ignored - only
    its minimum and maximum values will be considered. Mixtures in which
    the balance component amount falls outside its min and max values will be
    filtered out of the design space. In other words, formulation_grids could
    look like:
    
    {'balance component':[0.8, 0.85, 0.9],
     'other component':[0.1, 0.2, 0.3, 0.4, 0.5]}
    
    and the result would be:
    
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
        space. descriptors' keys should match the keys of formulation_grids
    name: str
        name for the EnumeratedDesignSpace
    description: str
        description for the EnumeratedDesignSpace
    """

    # Check that the passed balance component is in the grid keys
    assert balance_component in list(formulation_grids.keys()), \
        "balance component must be in formulation_grids' keys"
    non_balance_comps = [comp for comp in list(formulation_grids.keys())
                         if comp != balance_component]
    non_balance_descriptors = [dd for dd in descriptors 
                               if dd.key != balance_component]
    non_balance_grids = {
        k: v for k, v in formulation_grids.items()
        if k in non_balance_comps
    }
    
    # Check that all grid values are between 0 and 1
    for kk, val_list in formulation_grids.items():
        assert all([x >= 0 for x in val_list]) and \
            all([x <= 1 for x in val_list]), \
            f'values in {kk} are not between 0 and 1'

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
    """[ALPHA] Given a list of multiple input EnumeratedDesignSpaces, create a new
    EnumeratedDesignSpace that is the Cartesian product of candidates from each
    input design space.
    
    Ultimate length will be the product of the number of candidates in each
    individual design space
    
    Parameters
    ----------
    design_space_list: List[EnumeratedDesignSpace]
        A list of EnumeratedDesignSpaces
    """
    
    assert 'join_key' not in [ds.data[0].keys() for ds in design_space_list], \
        '"join_key" cannot be a descriptor key when using this function'
    
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
