"""Variable definitions for Ara."""
from abc import abstractmethod
from typing import Type, Optional, List  # noqa: F401

from taurus.entity.link_by_uid import LinkByUID
from taurus.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties


class IngredientQuantityDimension(BaseEnumeration):
    """The dimension of an ingredient quantity
    """
    ABSOLUTE = "absolute"
    MASS = "mass"
    VOLUME = "volume"
    NUMBER = "number"


class Variable(PolymorphicSerializable['Variable']):
    """A variable that can be assigned values present in material histories.

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
            RootIdentifier
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))

        return res


class RootInfo(Serializable['RootInfo'], Variable):
    """Metadata from the root of the material history.

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
    """Attribute marked by an attribute template.

    Parameters
    ----------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    template: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    template = properties.Object(LinkByUID, 'template')
    typ = properties.String('type', default="attribute_by_template", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "template", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 template: LinkByUID):
        self.name = name
        self.headers = headers
        self.template = template


class AttributeByTemplateAfterProcessTemplate(
        Serializable['AttributeByTemplateAfterProcessTemplate'], Variable):
    """Attribute of an object that is marked by an attribute template and derives from a process
    marked by a locally unique object template.

    TODO: define "locally-unique"

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    attributeTemplate: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    processTemplate: LinkByUID
        process template that identifies the originating process
    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    attributeTemplate = properties.Object(LinkByUID, 'attributeTemplate')
    processTemplate = properties.Object(LinkByUID, 'processTemplate')
    typ = properties.String('type', default="attribute_after_process", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attributeTemplate", "processTemplate", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 attributeTemplate: LinkByUID,
                 processTemplate: LinkByUID):
        self.name = name
        self.headers = headers
        self.attributeTemplate = attributeTemplate
        self.processTemplate = processTemplate


class AttributeByTemplateAndObjectTemplate(
        Serializable['AttributeByTemplateAndObjectTemplate'], Variable):
    """Attribute marked by an attribute template and an object template.

    TODO: clarify documentation of use case here.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    attributeTemplate: LinkByUID
        attribute template that identifies the attribute to assign to the variable
    objectTemplate: LinkByUID
        template that identifies the associated object
    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    attributeTemplate = properties.Object(LinkByUID, 'attributeTemplate')
    objectTemplate = properties.Object(LinkByUID, 'objectTemplate')
    typ = properties.String('type', default="attribute_by_object", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "attributeTemplate", "objectTemplate", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 attributeTemplate: LinkByUID,
                 objectTemplate: LinkByUID):
        self.name = name
        self.headers = headers
        self.attributeTemplate = attributeTemplate
        self.objectTemplate = objectTemplate


class IngredientIdentifierByProcessTemplateAndName(
        Serializable['IngredientIdentifierByProcessAndName'], Variable):
    """Ingredient identifier associated with a process template and a name.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    processTemplate: LinkByUID
        process template associated with this ingredient identifier
    ingredientName: str
        name of ingredient
    scope: str
    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    processTemplate = properties.Object(LinkByUID, 'processTemplate')
    ingredientName = properties.String('ingredientName')
    scope = properties.String('scope')
    typ = properties.String('type', default="ing_id_by_process_and_name", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "processTemplate", "ingredientName", "scope", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 processTemplate: LinkByUID,
                 ingredientName: str,
                 scope: str):
        self.name = name
        self.headers = headers
        self.processTemplate = processTemplate
        self.ingredientName = ingredientName
        self.scope = scope


class IngredientLabelByProcessAndName(Serializable['IngredientLabelByProcessAndName'], Variable):
    """Define a boolean variable indicating whether a given label is applied to an in ingredient
    that is associated with a process template and a name.

    For example, a label might be "solvent" for the variable "is the ethanol being used as a
    solvent?".  Many such columns would then support the downstream analysis "get the volumetric
    average density of the solvents".

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    processTemplate: LinkByUID
        process template associated with this ingredient identifier
    ingredientName: str
        name of ingredient
    label: str
        label to test
    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    processTemplate = properties.Object(LinkByUID, 'processTemplate')
    ingredientName = properties.String('ingredientName')
    label = properties.String('label')
    typ = properties.String('type', default="ing_label_by_process_and_name", deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "processTemplate", "ingredientName", "label", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 processTemplate: LinkByUID,
                 ingredientName: str,
                 label: str):
        self.name = name
        self.headers = headers
        self.processTemplate = processTemplate
        self.ingredientName = ingredientName
        self.label = label


class IngredientQuantityByProcessAndName(
        Serializable['IngredientQuantityByProcessAndName'], Variable):
    """Get the dimension of the quantity in an ingredient that is associated with a process
    template and a name.

    Parameters
    ---------
    name: str
        a short human-readable name to use when referencing the variable
    headers: list[str]
        sequence of column headers
    processTemplate: LinkByUID
        process template associated with this ingredient identifier
    ingredientName: str
        name of ingredient
    quantity: str
        dimension of the ingredient quantity (e.g. absolute, number fraction...)
    """

    name = properties.String('name')
    headers = properties.List(properties.String, 'headers')
    processTemplate = properties.Object(LinkByUID, 'processTemplate')
    ingredientName = properties.String('ingredientName')
    quantityDimension = properties.Enumeration(IngredientQuantityDimension, 'quantityDimension')
    typ = properties.String('type', default="ing_quantity_by_process_and_name",
                            deserializable=False)

    def _attrs(self) -> List[str]:
        return ["name", "headers", "processTemplate", "ingredientName", "quantityDimension", "typ"]

    def __init__(self, *,
                 name: str,
                 headers: List[str],
                 processTemplate: LinkByUID,
                 ingredientName: str,
                 quantityDimension: str):
        self.name = name
        self.headers = headers
        self.processTemplate = processTemplate
        self.ingredientName = ingredientName
        self.quantityDimension = quantityDimension


class RootIdentifier(Serializable['RootIdentifier'], Variable):
    """Get the identifier for the root of the material history, by scope.

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
