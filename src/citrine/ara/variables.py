"""Variable definitions for Ara."""
from abc import abstractmethod
from typing import Type, Optional, List, Tuple, Union  # noqa: F401

from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID
from taurus.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


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


class Variable(PolymorphicSerializable['Variable']):
    """[ALPHA] A variable that can be assigned values present in material histories.

    Abstract type that returns the proper type given a serialized dict.
    """

    @abstractmethod
    def _attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        if "type" not in data:
            raise ValueError("Can only get types from dicts with a 'type' key")
        types: List[Type[Serializable]] = [
            RootInfo, AttributeByTemplate, AttributeByTemplateAfterProcessTemplate,
            AttributeByTemplateAndObjectTemplate, IngredientIdentifierByProcessTemplateAndName,
            IngredientLabelByProcessAndName, IngredientQuantityByProcessAndName,
            RootIdentifier, AttributeInOutput
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))

        return res


class RootInfo(Serializable['RootInfo'], Variable):
    """[ALPHA] Metadata from the root of the material history.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    field: str
        name of the field to assign the variable to

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    field = properties.String('field')
    typ = properties.String('type', default="root_info", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "field", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 field: str):
        self.name = name
        self.headers = headers
        self.field = field


class AttributeByTemplate(Serializable['AttributeByTemplate'], Variable):
    """[ALPHA] Attribute marked by an attribute template.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    template: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    attribute_constraints: list[(LinkByUID, Bounds)]
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.

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
    typ = properties.String('type', default="attribute_by_template", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "template", "attribute_constraints", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 template: LinkByUID,
                 attribute_constraints: Optional[List[List[Union[LinkByUID, BaseBounds]]]] = None):
        self.name = name
        self.headers = headers
        self.template = template
        self.attribute_constraints = attribute_constraints


class AttributeByTemplateAfterProcessTemplate(
        Serializable['AttributeByTemplateAfterProcessTemplate'], Variable):
    """[ALPHA] Attribute of an object marked by an attribute template and a parent process template.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    attribute_template: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    process_template: LinkByUID
        process template that identifies the originating process
    attribute_constraints: list[(LinkByUID, Bounds)]
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.

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
    typ = properties.String('type', default="attribute_after_process", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attribute_template", "process_template",
                "attribute_constraints", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 attribute_template: LinkByUID,
                 process_template: LinkByUID,
                 attribute_constraints: Optional[List[List[Union[LinkByUID, BaseBounds]]]] = None):
        self.name = name
        self.headers = headers
        self.attribute_template = attribute_template
        self.process_template = process_template
        self.attribute_constraints = attribute_constraints


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
    attribute_template: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    object_template: LinkByUID
        template that identifies the associated object
    attribute_constraints: list[(LinkByUID, Bounds)]
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.

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
    typ = properties.String('type', default="attribute_by_object", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attribute_template", "object_template",
                "attribute_constraints", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 attribute_template: LinkByUID,
                 object_template: LinkByUID,
                 attribute_constraints: List[List[Union[LinkByUID, BaseBounds]]] = None):
        self.name = name
        self.headers = headers
        self.attribute_template = attribute_template
        self.object_template = object_template
        self.attribute_constraints = attribute_constraints


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

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    scope = properties.String('scope')
    typ = properties.String('type', default="ing_id_by_process_and_name", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "scope", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 process_template: LinkByUID,
                 ingredient_name: str,
                 scope: str):
        self.name = name
        self.headers = headers
        self.process_template = process_template
        self.ingredient_name = ingredient_name
        self.scope = scope


class IngredientLabelByProcessAndName(Serializable['IngredientLabelByProcessAndName'], Variable):
    """[ALPHA] Define a boolean variable indicating whether a given label is applied.

    Matches by process template, ingredient name, and the label string to check.

    For example, a label might be "solvent" for the variable "is the ethanol being used as a
    solvent?".  Many such columns would then support the downstream analysis "get the volumetric
    average density of the solvents".

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

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    label = properties.String('label')
    typ = properties.String('type', default="ing_label_by_process_and_name", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "label", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 process_template: LinkByUID,
                 ingredient_name: str,
                 label: str):
        self.name = name
        self.headers = headers
        self.process_template = process_template
        self.ingredient_name = ingredient_name
        self.label = label


class IngredientQuantityByProcessAndName(
        Serializable['IngredientQuantityByProcessAndName'], Variable):
    """[ALPHA] Get the quantity of an ingredient associated with a process template and a name.

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
        dimension of the ingredient quantity: absolute quantity, number, mass, or volume fraction.
        valid options are defined by :class:`~citrine.ara.variables.IngredientQuantityDimension`

    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    process_template = properties.Object(LinkByUID, 'process_template')
    ingredient_name = properties.String('ingredient_name')
    quantity_dimension = properties.Enumeration(IngredientQuantityDimension, 'quantity_dimension')
    typ = properties.String('type', default="ing_quantity_by_process_and_name",
                            deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "process_template", "ingredient_name", "quantity_dimension",
                "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 process_template: LinkByUID,
                 ingredient_name: str,
                 quantity_dimension: IngredientQuantityDimension):
        self.name = name
        self.headers = headers
        self.process_template = process_template
        self.ingredient_name = ingredient_name
        self.quantity_dimension = quantity_dimension


class RootIdentifier(Serializable['RootIdentifier'], Variable):
    """[ALPHA] Get the identifier for the root of the material history, by scope.

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

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 scope: str):
        self.name = name
        self.headers = headers
        self.scope = scope


class AttributeInOutput(
        Serializable['AttributeInOutput'], Variable):
    """[ALPHA] Attribute marked by an attribute template in the trunk of the history tree.

    The search for an attribute that marks the given attribute template starts at the root
    of the material history tree and proceeds until any of the given process templates are reached.
    Those templates block the search from continuing into their ingredients but do not halt the
    search entirely. This variable definition allows attributes that are present both in output
    and the inputs of a process to be distinguished.

    For example, a material "paint" might be produced by mixing and then resting "pigments" and
    a "base".  The color of the pigments and base could be measured and recorded as attributes
    in addition to the color of the resulting paint.  To define a variable as the color of the
    resulting paint, AttributeInTrunk can be used with the mixing process included in the list
    of process templates.  Then, when the platform looks for colors, it won't traverse through
    the mixing process and hit the colors of the pigments and base as well, which would result
    in an ambiguous variable match.

    Unlike "AttributeByTemplateAfterProcess", AttributeInTrunk will also match on the color
    attribute of the pigments in the rows that correspond to those pigments.  This way, all the
    colors can be assigned to the same variable and rendered into the same columns in the table.

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
    attribute_constraints: list[(LinkByUID, Bounds)]
        constraints on object attributes in the target object that must be satisfied. Constraints
        are expressed as Bounds.  Attributes are expressed with links. The attribute that the
        variable is being set to may be the target of a constraint as well.

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
    typ = properties.String('type', default="attribute_in_trunk", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attribute_template", "process_templates",
                "attribute_constraints", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 attribute_template: LinkByUID,
                 process_templates: List[LinkByUID],
                 attribute_constraints: List[List[Union[LinkByUID, BaseBounds]]] = None):
        self.name = name
        self.headers = headers
        self.attribute_template = attribute_template
        self.process_templates = process_templates
        self.attribute_constraints = attribute_constraints
