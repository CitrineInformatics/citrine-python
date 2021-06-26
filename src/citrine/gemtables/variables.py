"""Variable definitions for GEM Tables."""
from abc import abstractmethod
from typing import Type, Optional, List, Union
from uuid import UUID

from deprecation import deprecated

from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template import ProcessTemplate
from gemd.entity.template.attribute_template import AttributeTemplate
from gemd.entity.template.base_template import BaseTemplate
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties
from citrine.resources.data_concepts import CITRINE_SCOPE, _make_link_by_uid


class IngredientQuantityDimension(BaseEnumeration):
    """[ALPHA] The dimension of an ingredient quantity.

    * ABSOLUTE corresponds to the absolute quantity
    * MASS corresponds to the mass fraction
    * VOLUME corresponds to the volume fraction
    * NUMBER corresponds to the number fraction
    """

    ABSOLUTE = "absolute"
    MASS = "mass"
    VOLUME = "volume"
    NUMBER = "number"


class DataObjectTypeSelector(BaseEnumeration):
    """[ALPHA] The strategy for selecting types to consider for variable matching.

    Variables can potentially match many objects in a material history, creating
    ambiguity around which value should be assigned. In particular, associated
    runs and specs often share attributes and thus will often match the same
    variable. To enable disambiguation in such circumstances, many variables allow
    specification of a `type_selector`, with the following choices:

    * RUN_ONLY only match run objects
    * SPEC_ONLY only match spec objects
    * PREFER_RUN match either run or spec objects, and if both types match
                 only return the result for runs
    * ANY match either run or spec objects, and if both types match
          return an ambiguous error result
    """

    RUN_ONLY = "run_only"
    SPEC_ONLY = "spec_only"
    PREFER_RUN = "prefer_run"
    ANY = "any"


class Variable(PolymorphicSerializable['Variable']):
    """[ALPHA] A variable that can be assigned values present in material histories.

    Abstract type that returns the proper type given a serialized dict.
    """

    @abstractmethod
    def _attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        return type(self) == type(other) and all([
            getattr(self, key) == getattr(other, key) for key in self._attrs()
        ])

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        if "type" not in data:
            raise ValueError("Can only get types from dicts with a 'type' key")
        types: List[Type[Serializable]] = [
            TerminalMaterialInfo, AttributeByTemplate, AttributeByTemplateAfterProcessTemplate,
            AttributeByTemplateAndObjectTemplate, IngredientIdentifierByProcessTemplateAndName,
            IngredientLabelByProcessAndName, IngredientLabelsSetByProcessAndName,
            IngredientQuantityByProcessAndName,
            TerminalMaterialIdentifier, AttributeInOutput, IngredientIdentifierInOutput,
            IngredientLabelsSetInOutput, IngredientQuantityInOutput, XOR
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))

        return res


class TerminalMaterialInfo(Serializable['TerminalMaterialInfo'], Variable):
    """[ALPHA] Metadata from the terminal material of the material history.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    field: str
        name of the field to assign the variable to, for example, "sample_type" would
        assign the sample type of the terminal material run

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    field = properties.String('field')
    typ = properties.String('type', default="root_info", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "field", "typ"]

    def __init__(self,
                 name: str, *,
                 headers: List[str],
                 field: str):
        self.name = name
        self.headers = headers
        self.field = field


@deprecated(deprecated_in="0.133.0", removed_in="2.0.0",
            details="RootInfo is deprecated in favor of TerminalMaterialInfo")
def RootInfo(name: str, *, headers: List[str], field: str) -> TerminalMaterialInfo:
    """[DEPRECATED] Use TerminalMaterialInfo instead."""
    return TerminalMaterialInfo(name=name, headers=headers, field=field)


class AttributeByTemplate(Serializable['AttributeByTemplate'], Variable):
    """[ALPHA] Attribute marked by an attribute template.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    template: Union[UUID, str, LinkByUID, AttributeTemplate]
        attribute template that identifies the attribute to assign to the variable
    attribute_constraints: list[list[Union[UUID, str, LinkByUID, AttributeTemplate], Bounds]]
        Optional
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    template = properties.Object(LinkByUID, 'template')
    attribute_constraints = properties.Optional(
        properties.List(
            properties.SpecifiedMixedList(
                [properties.Object(LinkByUID), properties.Object(BaseBounds)]
            )
        ), 'attribute_constraints')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="attribute_by_template", deserializable=False)

    attribute_type = Union[UUID, str, LinkByUID, AttributeTemplate]
    constraint_type = Union[attribute_type, BaseBounds]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "template", "attribute_constraints", "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 template: attribute_type,
                 attribute_constraints: Optional[List[List[constraint_type]]] = None,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.template = _make_link_by_uid(template)
        self.attribute_constraints = None if attribute_constraints is None \
            else [(_make_link_by_uid(x[0]), x[1]) for x in attribute_constraints]
        self.type_selector = type_selector


class AttributeByTemplateAfterProcessTemplate(
        Serializable['AttributeByTemplateAfterProcessTemplate'], Variable):
    """[ALPHA] Attribute of an object marked by an attribute template and a parent process template.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    attribute_template: Union[UUID, str, LinkByUID, AttributeTemplate]
        attribute template that identifies the attribute to assign to the variable
    process_template: Union[UUID, str, LinkByUID, ProcessTemplate]
        process template that identifies the originating process
    attribute_constraints: list[list[Union[UUID, str, LinkByUID, AttributeTemplate], Bounds]]
        Optional
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    attribute_template = properties.Object(LinkByUID, 'attribute_template')
    process_template = properties.Object(LinkByUID, 'process_template')
    attribute_constraints = properties.Optional(
        properties.List(
            properties.SpecifiedMixedList(
                [properties.Object(LinkByUID), properties.Object(BaseBounds)]
            )
        ), 'attribute_constraints')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="attribute_after_process", deserializable=False)

    attribute_type = Union[UUID, str, LinkByUID, AttributeTemplate]
    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]
    constraint_type = Union[attribute_type, BaseBounds]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attribute_template", "process_template",
                "attribute_constraints", "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 attribute_template: attribute_type,
                 process_template: process_type,
                 attribute_constraints: Optional[List[List[constraint_type]]] = None,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.attribute_template = _make_link_by_uid(attribute_template)
        self.process_template = _make_link_by_uid(process_template)
        self.attribute_constraints = None if attribute_constraints is None \
            else [(_make_link_by_uid(x[0]), x[1]) for x in attribute_constraints]
        self.type_selector = type_selector


class AttributeByTemplateAndObjectTemplate(
        Serializable['AttributeByTemplateAndObjectTemplate'], Variable):
    """[ALPHA] Attribute marked by an attribute template and an object template.

    For example, one property may be measured by two different measurement techniques.  In this
    case, that property would have the same attribute template.  Filtering by measurement
    templates, which identify the measurement techniques, disambiguates the technique used to
    measure that otherwise ambiguous property.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    attribute_template: Union[UUID, str, LinkByUID, AttributeTemplate]
        attribute template that identifies the attribute to assign to the variable
    object_template: Union[UUID, str, LinkByUID, BaseTemplate]
        template that identifies the associated object
    attribute_constraints: list[list[Union[UUID, str, LinkByUID, AttributeTemplate], Bounds]]
        Optional
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    attribute_template = properties.Object(LinkByUID, 'attribute_template')
    object_template = properties.Object(LinkByUID, 'object_template')
    attribute_constraints = properties.Optional(
        properties.List(
            properties.SpecifiedMixedList(
                [properties.Object(LinkByUID), properties.Object(BaseBounds)]
            )
        ), 'attribute_constraints')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="attribute_by_object", deserializable=False)

    attribute_type = Union[UUID, str, LinkByUID, AttributeTemplate]
    object_type = Union[UUID, str, LinkByUID, BaseTemplate]
    constraint_type = Union[attribute_type, BaseBounds]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attribute_template", "object_template",
                "attribute_constraints", "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 attribute_template: attribute_type,
                 object_template: object_type,
                 attribute_constraints: Optional[List[List[constraint_type]]] = None,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.attribute_template = _make_link_by_uid(attribute_template)
        self.object_template = _make_link_by_uid(object_template)
        self.attribute_constraints = None if attribute_constraints is None \
            else [(_make_link_by_uid(x[0]), x[1]) for x in attribute_constraints]
        self.type_selector = type_selector


class IngredientIdentifierByProcessTemplateAndName(
        Serializable['IngredientIdentifierByProcessAndName'], Variable):
    """[ALPHA] Ingredient identifier associated with a process template and a name.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    process_template: LinkByUID
        process template associated with this ingredient identifier
    ingredient_name: str
        name of ingredient
    scope: str
        scope of the identifier (default: the Citrine scope)
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    scope = properties.String('scope')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="ing_id_by_process_and_name", deserializable=False)

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "scope",
                "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 process_template: process_type,
                 ingredient_name: str,
                 scope: str,  # Note that the default is set server side
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.process_template = _make_link_by_uid(process_template)
        self.ingredient_name = ingredient_name
        self.scope = scope
        self.type_selector = type_selector


class IngredientLabelByProcessAndName(Serializable['IngredientLabelByProcessAndName'], Variable):
    """[ALPHA] A boolean variable indicating whether a given label is applied.

    Matches by process template, ingredient name, and the label string to check.

    For example, a column might indicate whether or not the ingredient "ethanol" is labeled as a
    "solvent" in the "second mixing" process.  Many such columns would then support the
    downstream analysis "get the volumetric average density of the solvents".

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    process_template: LinkByUID
        process template associated with this ingredient identifier
    ingredient_name: str
        name of ingredient
    label: str
        label to test
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    label = properties.String('label')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="ing_label_by_process_and_name", deserializable=False)

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "label",
                "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 process_template: process_type,
                 ingredient_name: str,
                 label: str,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.process_template = _make_link_by_uid(process_template)
        self.ingredient_name = ingredient_name
        self.label = label
        self.type_selector = type_selector


class IngredientLabelsSetByProcessAndName(
        Serializable['IngredientLabelsSetByProcessAndName'],
        Variable):
    """[ALPHA] The set of labels on an ingredient when used in a process.

    For example, the ingredient "ethanol" might be labeled "solvent", "alcohol" and "VOC".
    The column would then contain that set of strings.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    process_template: LinkByUID
        process template associated with this ingredient identifier
    ingredient_name: str
        name of ingredient

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    typ = properties.String('type',
                            default="ing_labels_set_by_process_and_name",
                            deserializable=False)

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 process_template: process_type,
                 ingredient_name: str):
        self.name = name
        self.headers = headers
        self.process_template = _make_link_by_uid(process_template)
        self.ingredient_name = ingredient_name


class IngredientQuantityByProcessAndName(
        Serializable['IngredientQuantityByProcessAndName'], Variable):
    """[ALPHA] The quantity of an ingredient associated with a process template and a name.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    process_template: LinkByUID
        process template associated with this ingredient identifier
    ingredient_name: str
        name of ingredient
    quantity_dimension: IngredientQuantityDimension
        Dimension of the ingredient quantity: absolute quantity, number, mass, or volume fraction.
        Valid options are defined by
        :class:`~citrine.gemtables.variables.IngredientQuantityDimension`
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN
    unit: str
        An optional unit: only ingredient quantities that are convertible to this unit will be
        matched. Note that this parameter is mandatory when quantity_dimension is
        IngredientQuantityDimension.ABSOLUTE.

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    quantity_dimension = properties.Enumeration(IngredientQuantityDimension, 'quantity_dimension')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="ing_quantity_by_process_and_name",
                            deserializable=False)
    unit = properties.Optional(properties.String, "unit")

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "quantity_dimension",
                "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 process_template: process_type,
                 ingredient_name: str,
                 quantity_dimension: IngredientQuantityDimension,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN,
                 unit: Optional[str] = None):
        self.name = name
        self.headers = headers
        self.process_template = _make_link_by_uid(process_template)
        self.ingredient_name = ingredient_name
        self.type_selector = type_selector

        # Cast to make sure the string is valid
        if not isinstance(quantity_dimension, IngredientQuantityDimension):
            quantity_dimension = IngredientQuantityDimension.get_enum(quantity_dimension)
        self.quantity_dimension = quantity_dimension

        if quantity_dimension == IngredientQuantityDimension.ABSOLUTE:
            if unit is None:
                raise ValueError("Absolute Quantity variables require that 'unit' is set")
        else:
            if unit is not None and unit != "":
                raise ValueError("Fractional variables cannot take a 'unit'")
        self.unit = unit


class TerminalMaterialIdentifier(Serializable['TerminalMaterialIdentifier'], Variable):
    """[ALPHA] A unique identifier of the terminal material of the material history, by scope.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    scope: string
        scope of the identifier (default: the Citrine scope)

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    scope = properties.String('scope')
    typ = properties.String('type', default="root_id", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "scope", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 scope: str = CITRINE_SCOPE):
        self.name = name
        self.headers = headers
        self.scope = scope


@deprecated(deprecated_in="0.133.0", removed_in="2.0.0",
            details="RootIdentifier is deprecated in favor of TerminalMaterialIdentifier")
def RootIdentifier(name: str, *,
                   headers: List[str],
                   scope: str = CITRINE_SCOPE) -> TerminalMaterialIdentifier:
    """[DEPRECATED] Use TerminalMaterialIdentifier instead."""
    return TerminalMaterialIdentifier(name=name, headers=headers, scope=scope)


class AttributeInOutput(Serializable['AttributeInOutput'], Variable):
    """[ALPHA] Attribute marked by an attribute template in the trunk of the history tree.

    The search for an attribute that marks the given attribute template starts at the terminal
    of the material history tree and proceeds until any of the given process templates are reached.
    Those templates block the search from continuing into their ingredients but do not halt the
    search entirely. This variable definition allows attributes that are present both in output
    and the inputs of a process to be distinguished.

    For example, a material "paint" might be produced by mixing and then resting "pigments" and
    a "base".  The color of the pigments and base could be measured and recorded as attributes
    in addition to the color of the resulting paint. To define a variable as the color of the
    resulting paint, AttributeInOutput can be used with the mixing process included in the list
    of process templates. Then, when the platform looks for the color of a paint, it will find it
    but *won't* traverse through the mixing process and also find the colors of the pigments and
    base, which would result in an ambiguous variable match.

    Unlike "AttributeByTemplateAfterProcess", AttributeInOutput will also match on the color
    attribute of the pigments in the rows that correspond to those pigments. This way, all the
    colors can be assigned to the same variable and rendered into the same columns in the GEM
    table.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    attribute_template: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    process_templates: list[LinkByUID]
        process templates that should not be traversed through when searching for a matching
        attribute.  The attribute may be present in these processes but not their ingredients.
    attribute_constraints: list[list[Union[UUID, str, LinkByUID, AttributeTemplate], Bounds]]
        Optional
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    attribute_template = properties.Object(LinkByUID, 'attribute_template')
    process_templates = properties.List(properties.Object(LinkByUID), 'process_templates')
    attribute_constraints = properties.Optional(
        properties.List(
            properties.SpecifiedMixedList(
                [properties.Object(LinkByUID), properties.Object(BaseBounds)]
            )
        ), 'attribute_constraints')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="attribute_in_trunk", deserializable=False)

    attribute_type = Union[UUID, str, LinkByUID, AttributeTemplate]
    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]
    constraint_type = Union[attribute_type, BaseBounds]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attribute_template", "process_templates",
                "attribute_constraints", "type_selector", "typ"]

    def __init__(self,
                 name: str,
                 *,
                 headers: List[str],
                 attribute_template: attribute_type,
                 process_templates: List[process_type],
                 attribute_constraints: Optional[List[List[constraint_type]]] = None,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.attribute_template = _make_link_by_uid(attribute_template)
        self.process_templates = [_make_link_by_uid(x) for x in process_templates]
        self.attribute_constraints = None if attribute_constraints is None \
            else [(_make_link_by_uid(x[0]), x[1]) for x in attribute_constraints]
        self.type_selector = type_selector


class IngredientIdentifierInOutput(Serializable['IngredientIdentifierInOutput'], Variable):
    """[ALPHA] Ingredient identifier in the trunk of a material history tree.

    The search for an ingredient starts at the terminal of the material history tree and
    proceeds until any of the given process templates are reached. Those templates block the search
    from continuing but are inclusive: a match is extracted if an ingredient with the specified
    ingredient name is found at or before a cutoff.

    This variable definition allows an identifier to be extracted when an ingredient is used
    in multiple processes. As an example, consider a paint formed by mixing red and yellow
    pigments, where the red pigment is formed by mixing yellow and magenta. This variable could be
    used to represent the identifier of yellow in both mixing processes (red and the final paint)
    in a single column provided the process templates that mixed red and the final paint
    are included as cutoffs.

    In general, this variable should be preferred over an
    :class:`~citrine.gemtables.variables.IngredientIdentifierByProcessTemplateAndName` when
    mixtures are hierarchical (i.e., blends of blends).
    It allows an ingredient with a single name to be used in
    multiple processes without defining additional variables that manifest as additional columns
    in your GEM table, and must be used in place of the former if the same process template is
    used to represent mixing at multiple levels in the material history hierarchy. Going back
    to the previous example, this variable must be used in place of an
    :class:`~citrine.gemtables.variables.IngredientIdentifierByProcessTemplateAndName` if the same
    process template was used to represent the process that mixed red and the final paint.
    Using :class:`~citrine.gemtables.variables.IngredientIdentifierByProcessTemplateAndName`
    would result in an ambiguous match because yellow would be found twice in the
    material history, once when mixing red and again when mixing the final paint.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    ingredient_name: str
        Name of the ingredient to search for
    process_templates: list[Union[UUID, str, LinkByUID, ProcessTemplate]]
        Process templates halt the search for a matching ingredient name.
        These process templates are inclusive.
        The ingredient may be present in these processes but not before.
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    ingredient_name = properties.String('ingredient_name')
    process_templates = properties.List(properties.Object(LinkByUID), 'process_templates')
    scope = properties.String('scope')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    typ = properties.String('type', default="ing_id_in_output", deserializable=False)

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "ingredient_name", "process_templates", "scope",
                "type_selector", "typ"]

    def __init__(self,
                 name: str, *,
                 headers: List[str],
                 ingredient_name: str,
                 process_templates: List[process_type],
                 scope: str = CITRINE_SCOPE,
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN):
        self.name = name
        self.headers = headers
        self.ingredient_name = ingredient_name
        self.process_templates = [_make_link_by_uid(x) for x in process_templates]
        self.scope = scope
        self.type_selector = type_selector


class IngredientLabelsSetInOutput(Serializable['IngredientLabelsSetInOutput'], Variable):
    """[ALPHA] The set of labels on an ingredient in the trunk of a material history tree.

    The search for an ingredient starts at the terminal of the material history tree and proceeds
    until any of the given process templates are reached. Those templates block the search from
    continuing but are inclusive: a match is extracted if an ingredient with the specified
    ingredient name is found at or before a cutoff.

    This variable definition allows a set of labels to be extracted when an ingredient is used
    in multiple processes. As an example, consider a paint formed by mixing red and yellow
    pigments, where the red pigment is formed by mixing yellow and magenta. This variable could be
    used to represent the labels applied to yellow in both mixing processes (red and the final
    paint) in a single column provided the process templates that mixed red and the final paint
    are included as cutoffs.

    In general, this variable should be preferred over an
    :class:`~citrine.gemtables.variables.IngredientLabelsSetByProcessAndName` when
    mixtures are hierarchical (i.e., blends of blends).
    It allows an ingredient with a single name to be used in
    multiple processes without defining additional variables that manifest as additional columns
    in your GEM table, and must be used in place of the former if the same process template is
    used to represent mixing at multiple levels in the material history hierarchy. Going back
    to the previous example, this variable must be used in place of an
    :class:`~citrine.gemtables.variables.IngredientLabelsSetByProcessAndName` if the same
    process template was used to represent the process that mixed red and the final paint.
    Using :class:`~citrine.gemtables.variables.IngredientLabelsSetByProcessAndName`
    would result in an ambiguous match because yellow would be found twice in the
    material history, once when mixing red and again when mixing the final paint.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    process_templates: list[Union[UUID, str, LinkByUID, ProcessTemplate]]
        process templates that should not be traversed through when searching for a matching
        attribute.  The attribute may be present in these processes but not their ingredients.
    ingredient_name: str
        name of ingredient

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_templates = properties.List(properties.Object(LinkByUID), 'process_templates')
    ingredient_name = properties.String('ingredient_name')
    typ = properties.String('type', default="ing_label_set_in_output", deserializable=False)

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_templates", "ingredient_name", "typ"]

    def __init__(self,
                 name: str, *,
                 headers: List[str],
                 process_templates: List[process_type],
                 ingredient_name: str):
        self.name = name
        self.headers = headers
        self.process_templates = [_make_link_by_uid(x) for x in process_templates]
        self.ingredient_name = ingredient_name


class IngredientQuantityInOutput(Serializable['IngredientQuantityInOutput'], Variable):
    """[ALPHA] Ingredient quantity in the trunk of a material history tree.

    The search for an ingredient starts at the terminal of the material history tree and proceeds
    until any of the given process templates are reached. Those templates block the search from
    continuing but are inclusive: a match is extracted if an ingredient with the specified
    ingredient name is found at or before a cutoff.

    This variable definition allows a quantity to be extracted when an ingredient is used in
    multiple processes. As an example, consider a paint formed by mixing red and yellow pigments,
    where the red pigment is formed by mixing yellow and magenta. This variable could be used to
    represent the quantity of yellow in both mixing processes (red and the final paint) in a
    single column provided the process templates that mixed red and the final paint
    are included as cutoffs.

    In general, this variable should be preferred over an
    :class:`~citrine.gemtables.variables.IngredientQuantityByProcessTemplateAndName`
    when mixtures are hierarchical (i.e., blends of blends). It allows an ingredient with a
    single name to be used in multiple processes without defining additional variables
    that manifest as additional columns in your table, and must be used in place of the
    former if the same process template is used to represent mixing at multiple levels
    in the material history hierarchy.
    Going back to the previous example, this variable must be used in place of an
    :class:`~citrine.gemtables.variables.IngredientQuantityByProcessTemplateAndName` if the same
    process template was used to represent the process that mixed red and the final paint.
    Using :class:`~citrine.gemtables.variables.IngredientQuantityByProcessTemplateAndName`
    would result in an ambiguous match because yellow would be found twice in the material history,
    once when mixing red and again when mixing the final paint.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    ingredient_name: str
        Name of the ingredient to search for
    quantity_dimension: IngredientQuantityDimension
        Dimension of the ingredient quantity: absolute quantity, number, mass, or volume fraction.
        Valid options are defined by
        :class:`~citrine.gemtables.variables.IngredientQuantityDimension`
    process_templates: list[Union[UUID, str, LinkByUID, ProcessTemplate]]
        Process templates halt the search for a matching ingredient name.
        These process templates are inclusive.
        The ingredient may be present in these processes but not before.
    type_selector: DataObjectTypeSelector
        strategy for selecting data object types to consider when matching, defaults to PREFER_RUN
    unit: str
        an optional unit: only ingredient quantities that are convertible to this unit will be
        matched. note that this parameter is mandatory when quantity_dimension is
        IngredientQuantityDimension.ABSOLUTE.

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    ingredient_name = properties.String('ingredient_name')
    quantity_dimension = properties.Enumeration(IngredientQuantityDimension, 'quantity_dimension')
    process_templates = properties.List(properties.Object(LinkByUID), 'process_templates')
    type_selector = properties.Enumeration(DataObjectTypeSelector, "type_selector")
    unit = properties.Optional(properties.String, "unit")
    typ = properties.String('type', default="ing_quantity_in_output", deserializable=False)

    process_type = Union[UUID, str, LinkByUID, ProcessTemplate]

    def _attrs(self) -> List[str]:
        return ["name",
                "headers",
                "ingredient_name",
                "process_templates",
                "type_selector",
                "unit",
                "typ"]

    def __init__(self,
                 name: str, *,
                 headers: List[str],
                 ingredient_name: str,
                 quantity_dimension: IngredientQuantityDimension,
                 process_templates: List[process_type],
                 type_selector: DataObjectTypeSelector = DataObjectTypeSelector.PREFER_RUN,
                 unit: Optional[str] = None):
        self.name = name
        self.headers = headers
        self.ingredient_name = ingredient_name
        self.process_templates = [_make_link_by_uid(x) for x in process_templates]
        self.type_selector = type_selector

        # Cast to make sure the string is valid
        if not isinstance(quantity_dimension, IngredientQuantityDimension):
            quantity_dimension = IngredientQuantityDimension.get_enum(quantity_dimension)
        self.quantity_dimension = quantity_dimension

        if quantity_dimension == IngredientQuantityDimension.ABSOLUTE:
            if unit is None:
                raise ValueError("Absolute Quantity variables require that 'unit' is set")
        else:
            if unit is not None and unit != "":
                raise ValueError("Fractional variables cannot take a 'unit'")
        self.unit = unit


class XOR(Serializable['XOR'], Variable):
    """[ALPHA] Logical exclusive OR for GEM table variables.

    This variable combines the results of 2 or more variables into a single variable according to
    exclusive OR logic. XOR is defined when exactly one of its inputs is defined. Otherwise it is
    undefined.

    XOR can only operate on inputs with the same output type. For example, you may XOR
    :class:`~citrine.gemtables.variables.TerminalMaterialIdentifier` with
    :class:`~citrine.gemtables.variables.IngredientIdentifierByProcessTemplateAndName`
    because they both produce simple strings, but not with
    :class:`~citrine.gemtables.variables.IngredientQuantityInOutput`
    which produces a real numeric quantity.

    The input variables to XOR need not exist elsewhere in the table config, and the name and
    headers assigned to them have no bearing on how the table is constructed. That they are
    required at all is simply a limitation of the current API.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    variables: list[Variable]
        set of 2 or more Variables to XOR

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    variables = properties.List(properties.Object(Variable), 'variables')
    typ = properties.String('type', default="xor", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "variables", "typ"]

    def __init__(self, name, *, headers, variables):
        self.name = name
        self.headers = headers
        self.variables = variables
