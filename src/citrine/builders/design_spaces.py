import pandas as pd
from itertools import product

def EnumeratedProductDesignSpaceData(dof_grids:dict):
    ''' Given a dict of lists or tuples of values for each degree of freedom,
    create the list of candidates representing the outer product of all values
    for each degree of freedom
    
    Parameters
    ----------
    dof_grids: dict(str:list)
        {'degree of freedom':[list, of, values]} for each DoF
    '''
    design_space_tuples = list(product(*dof_grids.values()))
    design_space_cols = list(dof_grids.keys())
    df_ds = pd.DataFrame(data=design_space_tuples, columns=design_space_cols)
    candidates = df_ds.to_dict('records')
    return candidates


def SimpleMixtureProductDesignSpaceData(formulation_grids:dict,
                                        balance_component:str
                                        ):
    ''' Given a dict of lists or tuples of ingredient amounts (must be
    fractions of some kind, i.e. between 0-1), create
    a DataFrame that is the outer product of all possible combinations of
    ingredients *except* for the balance_component. The balance_component
    will then be filled in as 1-(all other ingredients) for each row.
    
    Many points generated through this process will be invalid (negative
    balance ingredient amount). These rows are filtered out as a last step,
    if the balance ingredient amount is below the lowest value in its list
    in formulation_grids, or above its highest value in that list (i.e.
    the limits do not have to be 0-1).
    
    Parameters
    ----------
    formulation_grids: dict
        {'component name':[list, of, values]} for each component
    balance_component: str
        name of the component that should make up the balance of the
        formulation (1-others). Must be a key in formulation_grids.
    '''

    assert balance_component in list(formulation_grids.keys()), \
        "balance component must be in formulation_grids' keys"
    non_balance_comps = [comp for comp in list(formulation_grids.keys())
                         if comp!=balance_component]

    # Start by making a naive product design space of non-balance components
    form_ds = pd.DataFrame(
        EnumeratedProductDesignSpaceData(
            {k:v for k,v in formulation_grids.items()
             if k in non_balance_comps}
        )
    )
    
    # Re-calculate the balance component column as 1-all others
    form_ds[balance_component] = form_ds.apply(
        lambda r: 1-sum([r[col] for col in non_balance_comps]),
        axis=1
    )
    
    # Order columns so balance component is first
    form_ds = form_ds[[balance_component]+non_balance_comps]
    
    # Eliminate out-of-range rows
    balance_range = (min(formulation_grids[balance_component]),
                     max(formulation_grids[balance_component])
    )
    form_ds = form_ds[form_ds[balance_component]>=balance_range[0]]
    form_ds = form_ds[form_ds[balance_component]<=balance_range[1]]
    data = form_ds.to_dict('records')

    return data


def JointDesignSpaceData(data_list:list):
    ''' Given multiple input design spaces (lists of candidates), create a
    set of candidates that is the outer product of candidates from each
    input design space.
    
    ultimate length will be len(data_list[0])*len(data_list[2])*...
    '''
    
    ds_list = [pd.DataFrame(data) for data in data_list]
    
    for df in ds_list:
        df['join_key']=0
    
    df_join=ds_list[0]
    for df in ds_list[1:]:
        df_join=pd.merge(df_join,df,on='join_key')
    df_join = df_join.drop(columns='join_key')
    data = df_join.to_dict('records')
    return data