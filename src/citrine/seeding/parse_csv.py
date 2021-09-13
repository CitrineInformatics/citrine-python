from gemd.entity.object import MaterialRun, MaterialSpec, ProcessRun, ProcessSpec, \
    MeasurementRun, MeasurementSpec, IngredientRun, IngredientSpec
from gemd.entity.object.base_object import BaseObject
from gemd.entity.value import NominalReal, NominalCategorical, NominalInteger, \
    InChI, Smiles, EmpiricalFormula
from gemd.entity.template import MaterialTemplate, ProcessTemplate, MeasurementTemplate, \
    PropertyTemplate, ConditionTemplate, ParameterTemplate
from gemd.entity.template.base_template import BaseTemplate
from gemd.entity.template.attribute_template import AttributeTemplate
from gemd.entity.bounds import RealBounds, CategoricalBounds, IntegerBounds, \
    MolecularStructureBounds, CompositionBounds
from gemd.entity.attribute import Property, Condition, Parameter
from gemd.entity.attribute.base_attribute import BaseAttribute

from collections import OrderedDict
from enum import Enum
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from typing import Any, Dict, Callable
import warnings


class FractionBasis(float, Enum):
    """
    Enumeration of normalization types for basis.

    Describes whether fractions are expressed in standard (sum-to-one) format,
    percentage (sum-to-100) or unnormalized (don't check, just normalize) format.
    """

    NOT_NORMALIZED = -1.0
    STANDARD = 1.0
    PERCENT = 100.0


def is_binary_series(series: pd.Series):
    """Test if the structure of a column is compatible with a binary feature."""
    # Good: 1, 0, 1.0, 0.0, 1., 0., 0.0000, 1.0000
    # Bad:  0.00001, 1.000001, 2.0, etc..
    if is_numeric_dtype(series):
        return series.dropna().isin([0, 1]).all()
    else:
        # Note that True/False look binary, but would cause the str cast to fail
        mask = (series == True) | (series == False)  # noqa: E712  is doesn't broadcast
        return series.mask(mask, np.nan).dropna().str.match(r"^\s*[01](?:\.0*)?(\s)*(?!.)").all()


def is_binary_attribute(tmpl: AttributeTemplate):
    """Evaluate if a template is consistent with a binary attribute."""
    binary_bounds = IntegerBounds(lower_bound=0, upper_bound=1)
    return binary_bounds.contains(tmpl.bounds)


def fill_binary(df: pd.DataFrame, *, value=0.0):
    """
    Fill NaN values in all binary columns of a dataframe with a value.

    Note that even though the dataframe is returned, the edit is also made inplace.


    Parameters
    ----------
    df: DataFrame
        The DataFrame to modify.
    value
        Value to use to fill NaN cells. Defaults to 0.0.

    Returns
    -------
    DataFrame
        The resulting dataframe.

    """
    for col in df:
        if is_binary_series(df[col]):
            df[col] = df[col].fillna(value)
    return df


def guess_attribute_templates(scope: str, df: pd.DataFrame) -> Dict[str, AttributeTemplate]:
    """Generates attribute template guesses & attribute builders based on a dataframe."""
    import re

    attr_tmpls = OrderedDict()
    for col in df:
        if re.match("PROPERTY:", col, re.IGNORECASE):
            word = "PROPERTY"
            typ = PropertyTemplate
        elif re.match("PREPARATION STEP DETAIL:", col, re.IGNORECASE):
            word = "PREPARATION STEP DETAIL"
            typ = ConditionTemplate
        else:
            # not an attribute
            continue  # pragma: no cover  https://github.com/nedbat/coveragepy/issues/198

        # No data, also skip
        if df[col].isnull().all():
            warnings.warn("Skipping column '{}' with no entries.".format(col))
            continue

        pattern = r"{}:\s*([^()]*?)\s*(?:\(([^()]*)\))?\s*$".format(word)

        res = re.match(pattern, col, re.IGNORECASE)
        if not res:
            raise ValueError("Column match fail: {}->{}".format(word, col))
        name, units = res.groups()
        if units is None:
            units = ""

        # Guess column bounds
        if is_binary_series(df[col]):
            attr_tmpls[col] = typ(name=name, bounds=IntegerBounds(lower_bound=0, upper_bound=1))
        elif is_numeric_dtype(df[col]):
            from math import ceil, log10, pow

            abs_max = max(df[col].max(), -df[col].min())
            if abs_max == 0:
                digits = 0  # pragma: no cover  Unreachable b/c it'd be a binary series
            else:
                digits = ceil(log10(abs_max) + 0.3)  # In case it's close to a power of 10

            if df[col].min() < 0:
                min_val = -pow(10, digits)
            else:
                min_val = 0
            if df[col].max() > 0:
                max_val = pow(10, digits)
            else:
                max_val = 0

            attr_tmpls[col] = typ(
                name=name,
                uids={scope: name},
                bounds=RealBounds(lower_bound=min_val, upper_bound=max_val, default_units=units),
            )
        else:
            cats = df[df[col].notna()][col].unique().astype(str)
            attr_tmpls[col] = typ(name=name, bounds=CategoricalBounds(categories=cats))

    return attr_tmpls


def attribute_template_to_builder(template: AttributeTemplate) -> Callable[[Any], BaseAttribute]:
    """Returns a method that builds attributes consistent with a given Attribute Template."""
    attr_type = (
        # Note that we are not properly handling PropertyAndConditions objects
        Property if isinstance(template, PropertyTemplate)
        else Condition if isinstance(template, ConditionTemplate)
        else Parameter if isinstance(template, ParameterTemplate)
        else None
    )
    if attr_type is None:
        raise TypeError(
            "Unrecognized/Unhandled Attribute Template type: {}".format(type(template))
        )

    if isinstance(template.bounds, RealBounds):
        return lambda x: attr_type(
            name=template.name,
            template=template,
            value=NominalReal(nominal=x, units=template.bounds.default_units),
        )

    if isinstance(template.bounds, CategoricalBounds):
        return lambda x: attr_type(
            name=template.name, template=template, value=NominalCategorical(category=x)
        )

    if isinstance(template.bounds, IntegerBounds):
        return lambda x: attr_type(
            name=template.name, template=template, value=NominalInteger(nominal=round(float(x)))
        )

    if isinstance(template.bounds, MolecularStructureBounds):

        def _molecule_type(x):
            if x.startswith("InChI="):  # Standard format for all InChI strings
                return InChI(inchi=x)
            else:
                return Smiles(smiles=x)

        return lambda x: attr_type(name=template.name, template=template, value=_molecule_type(x))

    if isinstance(template.bounds, CompositionBounds):
        return lambda x: attr_type(
            name=template.name, template=template, value=EmpiricalFormula(formula=x)
        )

    # Unreachable guard for future development
    msg = f"Unrecognized/Unhandled Bounds type: {type(template.bounds)}"  # pragma: no cover
    raise TypeError(msg)  # pragma: no cover


def guess_object_templates(
        scope: str, df: pd.DataFrame, *, attr_tmpls: Dict[str, AttributeTemplate] = None
) -> Dict[str, BaseTemplate]:
    """Generates object template guesses & linking based on a dataframe."""
    import re

    if attr_tmpls is None:
        attr_tmpls = guess_attribute_templates(scope, df)

    obj_tmpls = OrderedDict()

    # Match the necessary columns to that we're not case sensitive
    # Get the case-insensitive column labels
    name_header = next(x for x in df if re.match(r"IDENTIFIER:\s*name", x, re.IGNORECASE))
    class_header = next(
        x for x in df if re.match(r"CLASSIFICATION:\s*component\s+type", x, re.IGNORECASE)
    )
    process_headers = [x for x in df if re.match(r"PREPARATION\s+STEP\s+NAME", x, re.IGNORECASE)]

    max_id = max(
        (
            int(y.group(1))
            for y in [re.match(r"SUBSYSTEM\s+(\d+)", x, re.IGNORECASE) for x in df]
            if y
        ),
        default=-1,
    )
    ing_name_tmpl = next(
        (
            y.group(0).replace(y.group(1), "{}")
            for y in [
                re.match(r"SUBSYSTEM\s+(\d+)\s+IDENTIFIER:\s*name",
                         x, re.IGNORECASE)
                for x in df
            ]
            if y
        ),
        None,
    )
    subsystem_name_cols = [ing_name_tmpl.format(i) for i in range(max_id + 1)]

    for i_proc, process_header in enumerate(process_headers):
        this_iloc = df.columns.get_loc(process_header)
        if i_proc + 1 == len(process_headers):  # Last process
            next_loc = len(df.columns)
        else:
            next_loc = df.columns.get_loc(process_headers[i_proc+1])
        subset = df.iloc[:, this_iloc:next_loc]

        for process_name in subset[process_header].dropna().unique():
            if process_name in obj_tmpls:
                # Unreachable guard for future development
                raise ValueError(f"Collision in template name: {process_name}")  # pragma: no cover
            used_ingredients = subset[subset[process_header] == process_name][
                subsystem_name_cols
            ].values.ravel()
            unique_ingredients = np.unique(used_ingredients[~pd.isnull(used_ingredients)])
            used_labels = df.loc[df[name_header].isin(unique_ingredients)][class_header].unique()

            obj_tmpls[process_name] = ProcessTemplate(
                name=process_name,
                uids={scope: process_name},
                allowed_names=["Subsystem {}".format(i) for i in range(max_id + 1)],
                allowed_labels=list(used_labels),
            )
            for col in attr_tmpls:
                if "PROCESS" not in col or col not in subset:
                    continue
                if any((subset[process_header] == process_name) & (subset[col].notna())):
                    print(process_name, col, type(attr_tmpls[col]))
                    obj_tmpls[process_name].conditions.append(attr_tmpls[col])

    for material_name in df[class_header].dropna().unique():
        if material_name in obj_tmpls:
            raise ValueError("Collision in template name: {}".format(material_name))
        obj_tmpls[material_name] = MaterialTemplate(
            name=material_name, uids={scope: material_name}
        )
        # Assume no attributes for Material Templates at this time

    # Now we need to figure out which measurements are clustered
    measurements_queue = [col for col in attr_tmpls if re.match("PROPERTY:", col, re.IGNORECASE)]
    while measurements_queue:
        lead = measurements_queue.pop(0)
        full = [lead]
        for candidate in measurements_queue:
            if all((df[lead].isna()) ^ (df[candidate].notna())):
                full.append(candidate)
        for x in full[1:]:
            measurements_queue.remove(x)
        measurements_name = "-".join([attr_tmpls[x].name for x in full]) + " Measurement"
        obj_tmpls[measurements_name] = MeasurementTemplate(
            name=measurements_name, uids={scope: measurements_name}
        )
        obj_tmpls[measurements_name].properties = [attr_tmpls[x] for x in full]

    return obj_tmpls


def objectify_rows(
        scope: str,
        df: pd.DataFrame,
        *,
        attr_tmpls: Dict[str, AttributeTemplate] = None,
        obj_tmpls: Dict[str, BaseTemplate] = None,
        fraction_basis: FractionBasis = FractionBasis.NOT_NORMALIZED,
) -> Dict[str, BaseObject]:
    """Generates objects based on a dataframe and set of templates."""
    import re

    if attr_tmpls is None:
        attr_tmpls = guess_attribute_templates(scope, df)
    if obj_tmpls is None:
        obj_tmpls = guess_object_templates(scope, df, attr_tmpls=attr_tmpls)

    links = dict()
    mat_index = OrderedDict()

    val_builder = {col: attribute_template_to_builder(attr_tmpls[col]) for col in attr_tmpls}
    tmpl_links = dict()
    inv_attr_tmpls = {v: k for k, v in attr_tmpls.items()}
    for obj_name, obj_tmpl in obj_tmpls.items():
        from gemd.entity.template.has_property_templates import HasPropertyTemplates
        from gemd.entity.template.has_condition_templates import HasConditionTemplates
        from gemd.entity.template.has_parameter_templates import HasParameterTemplates

        queue = []
        if isinstance(obj_tmpl, HasPropertyTemplates):
            queue += [x[0] for x in obj_tmpl.properties]
        if isinstance(obj_tmpl, HasConditionTemplates):
            queue += [x[0] for x in obj_tmpl.conditions]
        if isinstance(obj_tmpl, HasParameterTemplates):
            queue += [x[0] for x in obj_tmpl.parameters]

        for attr_tmpl in queue:
            tmpl_links[inv_attr_tmpls[attr_tmpl]] = obj_name

    # Get the case-insensitive column labels
    name_header = next(x for x in df if re.match(r"IDENTIFIER:\s*name", x, re.IGNORECASE))
    class_header = next(
        x for x in df if re.match(r"CLASSIFICATION:\s*component\s+type", x, re.IGNORECASE)
    )
    process_header = next(
        x for x in df if re.match(r"PREPARATION\s+STEP\s+NAME", x, re.IGNORECASE)
    )
    ing_name_tmpl = next(
        (
            y.group(0).replace(y.group(1), "{}")
            for y in [
                re.match(r"SUBSYSTEM\s+(\d+)\s+IDENTIFIER:\s*name",
                         x, re.IGNORECASE)
                for x in df
            ]
            if y
        ),
        None,
    )
    ing_amt_tmpl = next(
        (
            y.group(0).replace(y.group(1), "{}")
            for y in [
                re.match(r"SUBSYSTEM\s+(\d+)\s+ACTUAL\s+QUANTITY\s+\(mass\)",
                         x, re.IGNORECASE)
                for x in df
            ]
            if y
        ),
        None,
    )

    # Match the necessary columns to that we're not case sensitive
    max_id = max(
        (
            int(y.group(1))
            for y in [re.match(r"SUBSYSTEM\s+(\d+)", x, re.IGNORECASE) for x in df]
            if y
        ),
        default=-1,
    )

    for _, row in df.iterrows():
        mat_name = row[name_header]
        mat_run = MaterialRun(
            name=mat_name,
            uids={scope: mat_name},
            tags=["class::{}".format(row[class_header])],
            process=ProcessRun(name=row[process_header]),
        )
        mat_run.process.spec = ProcessSpec(
            name=mat_run.process.name, template=obj_tmpls[mat_run.process.name],
        )
        mat_run.spec = MaterialSpec(
            name=mat_run.name, process=mat_run.process.spec, template=obj_tmpls[row[class_header]],
        )

        if mat_name in mat_index:
            raise ValueError("Repeat material identifier: {}".format(mat_name))
        mat_index[mat_name] = mat_run

        links[mat_name] = []
        for i in range(max_id + 1):
            ing_name = ing_name_tmpl.format(i)
            ing_amt = ing_amt_tmpl.format(i)
            if pd.notnull(row[ing_name]):
                links[mat_name].append((row[ing_name], row[ing_amt]))

        row_msr = OrderedDict()
        for key in row.dropna().keys():
            if key not in val_builder:
                continue
            attr = val_builder[key](row[key])

            # Simplify here, since only certain types end up in certain places
            if isinstance(attr, Property):
                msr_name = tmpl_links[key]
                if msr_name not in row_msr:
                    msr_spec = MeasurementSpec(name=msr_name, template=obj_tmpls[msr_name])
                    msr_run = MeasurementRun(name=msr_name, material=mat_run, spec=msr_spec)
                    row_msr[msr_name] = msr_run
                else:
                    msr_run = row_msr[msr_name]
                msr_run.properties.append(attr)
            elif isinstance(attr, Condition):
                mat_run.process.conditions.append(attr)
            else:
                raise TypeError("Unhandled type: {}".format(type(attr)))

    for downstream in links:
        if fraction_basis == FractionBasis.NOT_NORMALIZED:
            total = sum(x[1] for x in links[downstream])
            if len(links[downstream]) > 0 and total <= 0.0:
                raise ValueError(f"Sum of ingredients to {downstream} was {total}")
        else:
            total = fraction_basis.value

        for i, (upstream, amount) in enumerate(links[downstream]):
            ing_name = "Subsystem {}".format(i)
            label_list = df.loc[df[name_header] == upstream][[class_header]].values.reshape(-1)

            ing_spec = IngredientSpec(
                name=ing_name,
                material=mat_index[upstream].spec,
                process=mat_index[downstream].spec.process,
                labels=list(label_list),
            )

            # TODO: Option for mass/number/volume/absolute
            ing_fraction = NominalReal(nominal=amount / total, units="")
            ing_run = IngredientRun(  # noqa: F841  Easier to follow w/ unused variable
                material=mat_index[upstream],
                spec=ing_spec,
                process=mat_index[downstream].process,
                mass_fraction=ing_fraction,
            )

    return mat_index
