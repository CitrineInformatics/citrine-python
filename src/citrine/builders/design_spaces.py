import pandas as pd
from itertools import product
from typing import Mapping, Sequence, Any


def enumerate_cartesian_product(
    dof_grids: Mapping[str, Sequence]
    ) -> Sequence[Mapping[str, Any]]:
    '''[ALPHA] Given a dict of lists or tuples of values for each degree of freedom,
    create the list of candidates representing the Cartesian product of all
    values for each degree of freedom

    Parameters
    ----------
    dof_grids: Mapping[str, Sequence]
        {'degree of freedom':[sequence, of, values]} for each DoF
    '''
    design_space_tuples = list(product(*dof_grids.values()))
    design_space_cols = list(dof_grids.keys())
    df_ds = pd.DataFrame(data=design_space_tuples, columns=design_space_cols)
    candidates = df_ds.to_dict('records')
    return candidates


def enumerate_simple_mixture_cartesian_product(
    formulation_grids:Mapping[str, Sequence[float]],
    balance_component:str
    ) -> Sequence[Mapping[str, float]]:
    '''[ALPHA] Given a dict of lists or tuples of ingredient amounts (must be
    fractions of some kind, i.e. between 0-1), create candidates that are
    the Cartesian product of all possible combinations of ingredients *except*
    for the balance_component. The balance_component will then be filled in
    as 1-(all other ingredients) for each row.
    
    The balance component's [list, of, values] can be similar to the other
    components'; in this way, the balance component can be swapped out easily.
    However, the balance component's discretization will be ignored - only
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
    '''

    assert balance_component in list(formulation_grids.keys()), \
        "balance component must be in formulation_grids' keys"
    non_balance_comps = [comp for comp in list(formulation_grids.keys())
                         if comp!=balance_component]

    # Start by making a naive product design space of non-balance components
    form_ds = pd.DataFrame(
        enumerate_cartesian_product(
            {k: v for k, v in formulation_grids.items()
             if k in non_balance_comps}
        )
    )
    
    # Re-calculate the balance component column as 1-all others
    form_ds[balance_component] = form_ds.apply(
        lambda r: 1-sum([r[col] for col in non_balance_comps]),
        axis= 1
    )
    
    # Order columns so balance component is first
    form_ds = form_ds[[balance_component]+non_balance_comps]
    
    # Eliminate out-of-range rows
    balance_range = (min(formulation_grids[balance_component]),
                     max(formulation_grids[balance_component])
    )
    form_ds = form_ds[form_ds[balance_component] >= balance_range[0]]
    form_ds = form_ds[form_ds[balance_component] <= balance_range[1]]
    data = form_ds.to_dict('records')

    return data


def cartesian_join_design_spaces(
    data_list: Sequence[Sequence[Mapping[str, Any]]]
    ) -> Sequence[Mapping[str, Any]]:
    ''' Given multiple input design spaces (lists of candidates), create a
    set of candidates that is the Cartesian product of candidates from each
    input design space.
    
    ultimate length will be len(data_list[0])*len(data_list[2])*...
    
    Parameters
    ----------
    data_list: Sequence[Sequence[Mapping[str, Any]]]
        A list of [lists of candidates] (data for individual design subspaces)
    '''
    
    assert 'join_key' not in [data[0].keys() for data in data_list], \
        '"join_key" cannot be a descriptor key when using this function'
    
    ds_list = [pd.DataFrame(data) for data in data_list]
    
    for df in ds_list:
        df['join_key'] = 0
    
    df_join = ds_list[0]
    for df in ds_list[1:]:
        df_join = pd.merge(df_join, df, on='join_key')
    df_join = df_join.drop(columns='join_key')
    data = df_join.to_dict('records')
    return data
