from itertools import chain
from typing import Iterator, Mapping

from gemd.entity.bounds import RealBounds, CategoricalBounds, MolecularStructureBounds, \
    IntegerBounds, CompositionBounds
from gemd.entity.template.attribute_template import AttributeTemplate
from gemd.entity.value import EmpiricalFormula

from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, \
    MolecularStructureDescriptor, Descriptor, ChemicalFormulaDescriptor
from citrine.resources.data_concepts import DataConceptsCollection
from citrine.resources.project import Project


class NoEquivalentDescriptorError(ValueError):
    """Error that is raised when the bounds in a template have no equivalent descriptor."""

    pass


def template_to_descriptor(template: AttributeTemplate) -> Descriptor:
    """
    Convert a GEMD attribute template into an AI Engine Descriptor.

    IntBounds cannot be converted because they have no matching descriptor type.
    CompositionBounds can only be converted when every component is an element, in which case
    they are converted to ChemicalFormulaDescriptors.

    Parameters
    ----------
    template: AttributeTemplate
        Template to convert into a descriptor

    Returns
    -------
    Descriptor
        Descriptor with a key matching the template name and type corresponding to the bounds

    """
    bounds = template.bounds
    if isinstance(bounds, RealBounds):
        return RealDescriptor(
            key=template.name,
            lower_bound=bounds.lower_bound,
            upper_bound=bounds.upper_bound,
            units=bounds.default_units
        )
    if isinstance(bounds, CategoricalBounds):
        return CategoricalDescriptor(
            key=template.name,
            categories=bounds.categories
        )
    if isinstance(bounds, MolecularStructureBounds):
        return MolecularStructureDescriptor(
            key=template.name
        )
    if isinstance(bounds, CompositionBounds):
        if set(bounds.components).issubset(EmpiricalFormula.all_elements()):
            return ChemicalFormulaDescriptor(
                key=template.name
            )
        else:
            msg = "Cannot create descriptor for CompositionBounds with non-atomic components"
            raise NoEquivalentDescriptorError(msg)
    if isinstance(bounds, IntegerBounds):
        raise NoEquivalentDescriptorError("Cannot create a descriptor for integer-valued data")
    raise ValueError("Template has unrecognized bounds: {}".format(type(bounds)))


class PlatformVocabulary(Mapping[str, Descriptor]):
    """
    Dictionary of descriptors that define a controlled vocabulary for the AI Engine.

    Parameters
    ----------
    entries: Mapping[str, Descriptor]
        Entries in the dictionary, indexed by a convenient name.
        To build from templates, use PlatformVocabulary.from_templates

    """

    def __init__(self, entries: Mapping[str, Descriptor]):
        self._entries = entries

    def __getitem__(self, k: str) -> Descriptor:
        return self._entries[k]

    def __len__(self):
        return len(self._entries)

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    @staticmethod
    def from_templates(project: Project, scope: str):
        """
        Build a PlatformVocabulary from the templates visible to a project.

        All of the templates with the given scope are downloaded and converted into descriptors.
        The uid values associated with that scope are used as the index into the dictionary.
        For example, using scope "my_templates" with a template with
        uids={"my_templates": "density"} would be indexed into the dictionary as "density".

        Parameters
        ----------
        project: Project
            Project on the Citrine Platform to read templates from
        scope: str
            Unique ID scope from which to pull the template names

        Returns
        -------
        PlatformVocabulary

        """
        def _from_collection(collection: DataConceptsCollection):
            return {x.uids[scope]: x for x in collection.list_all() if scope in x.uids}

        properties = _from_collection(project.property_templates)
        parameters = _from_collection(project.parameter_templates)
        conditions = _from_collection(project.condition_templates)

        res = {}
        for k, v in chain(properties.items(), parameters.items(), conditions.items()):
            try:
                desc = template_to_descriptor(v)
                res[k] = desc
            except NoEquivalentDescriptorError:
                continue

        return PlatformVocabulary(res)
