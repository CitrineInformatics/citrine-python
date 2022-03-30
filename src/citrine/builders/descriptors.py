from itertools import chain
from typing import Iterator, Mapping, Union, List
from uuid import UUID

from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.bounds import RealBounds, CategoricalBounds, MolecularStructureBounds, \
    IntegerBounds, CompositionBounds
from gemd.entity.template.attribute_template import AttributeTemplate
from gemd.entity.template.has_property_templates import HasPropertyTemplates
from gemd.entity.template.has_condition_templates import HasConditionTemplates
from gemd.entity.template.has_parameter_templates import HasParameterTemplates
from gemd.entity.value import EmpiricalFormula
from gemd.util import recursive_flatmap, set_uuids

from citrine.builders.auto_configure import AutoConfigureMode
from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, \
    MolecularStructureDescriptor, Descriptor, ChemicalFormulaDescriptor, IntegerDescriptor
from citrine.resources.data_concepts import DataConceptsCollection
from citrine.resources.material_run import MaterialRun
from citrine.resources.project import Project


class NoEquivalentDescriptorError(ValueError):
    """Error that is raised when the bounds in a template have no equivalent descriptor."""

    pass


def template_to_descriptor(template: AttributeTemplate, *,
                           headers: List[str] = []) -> Descriptor:
    """
    Convert a GEMD attribute template into an AI Engine Descriptor.

    IntBounds cannot be converted because they have no matching descriptor type.
    CompositionBounds can only be converted when every component is an element, in which case
    they are converted to ChemicalFormulaDescriptors.

    Parameters
    ----------
    template: AttributeTemplate
        Template to convert into a descriptor
    headers: List[str]
        Names of parent relationships to includes as prefixes
        to the template name in the descriptor key
        Default: []

    Returns
    -------
    Descriptor
        Descriptor with a key matching the template name and type corresponding to the bounds

    """
    headers = headers + [template.name]
    descriptor_key = '~'.join(headers)
    bounds = template.bounds
    if isinstance(bounds, RealBounds):
        return RealDescriptor(
            key=descriptor_key,
            lower_bound=bounds.lower_bound,
            upper_bound=bounds.upper_bound,
            units=bounds.default_units
        )
    if isinstance(bounds, CategoricalBounds):
        return CategoricalDescriptor(
            key=descriptor_key,
            categories=bounds.categories
        )
    if isinstance(bounds, MolecularStructureBounds):
        return MolecularStructureDescriptor(
            key=descriptor_key
        )
    if isinstance(bounds, CompositionBounds):
        if set(bounds.components).issubset(EmpiricalFormula.all_elements()):
            return ChemicalFormulaDescriptor(
                key=descriptor_key
            )
        else:
            msg = "Cannot create descriptor for CompositionBounds with non-atomic components"
            raise NoEquivalentDescriptorError(msg)
    if isinstance(bounds, IntegerBounds):
        return IntegerDescriptor(
            key=descriptor_key,
            lower_bound=bounds.lower_bound,
            upper_bound=bounds.upper_bound
        )
    raise ValueError("Template has unrecognized bounds: {}".format(type(bounds)))


class PlatformVocabulary(Mapping[str, Descriptor]):
    """
    Dictionary of descriptors that define a controlled vocabulary for the AI Engine.

    Parameters
    ----------
    entries: Mapping[str, Descriptor]
        Entries in the dictionary, indexed by a convenient name.
        To build from templates, use PlatformVocabulary.from_templates
        To build from a material, use PlatformVocabulary.from_material

    """

    def __init__(self, *, entries: Mapping[str, Descriptor]):
        self._entries = entries

    def __getitem__(self, k: str) -> Descriptor:
        return self._entries[k]

    def __len__(self):
        return len(self._entries)

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    @staticmethod
    def from_templates(*, project: Project, scope: str):
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
            return {x.uids[scope]: x for x in collection.list() if scope in x.uids}

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

        return PlatformVocabulary(entries=res)

    @staticmethod
    def from_material(
            *,
            project: Project,
            material: Union[str, UUID, LinkByUID, MaterialRun],
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            full_history: bool = True
    ):
        """[ALPHA] Build a PlatformVocabulary from templates appearing in a material history.

        All of the attribute templates that appear throughout the material's history
        are extracted and converted into descriptors.

        Descriptor keys are formatted according to the option set by mode.
        For example, if a condition template with name 'Condition 1'
        appears in a parent process with name 'Parent',
        the mode option produces the following descriptor key:

        mode = AutoConfigMode.PLAIN       --> 'Parent~Condition 1'
        mode = AutoConfigMode.FORMULATION --> 'Condition 1'

        Parameters
        ----------
        project: Project
            Project to use when accessing the Citrine Platform.
        material: Union[str, UUID, LinkByUID, MaterialRun]
            A representation of the material to extract descriptors from.
        mode: AutoConfigureMode
            Formatting option for descriptor keys in the platform vocabulary.
            Option AutoConfigMode.PLAIN includes headers from the parent object,
            whereas option AutoConfigMode.FORMULATION does not.
            Default: AutoConfigureMode.PLAIN
        full_history: bool
            Whether to extract descriptors from the full material history,
            or only the provided (terminal) material.
            Default: True

        Returns
        -------
        PlatformVocabulary

        """
        if not isinstance(mode, AutoConfigureMode):
            raise TypeError('mode must be an option from AutoConfigureMode')

        # Full history not needed when full_history = False
        # But is convenient to populate templates for terminal material
        history = project.material_runs.get_history(id=material)
        if full_history:
            search_history = recursive_flatmap(history, lambda x: [x], unidirectional=False)
            set_uuids(search_history, 'id')
        else:
            # Limit the search to contain the terminal material/process/measurements
            search_history = [history.spec.template, history.process.template]
            search_history.extend([msr.template for msr in history.measurements])
            search_history = [x for x in search_history if x is not None]  # Edge case safety

        # Extract templates and formatted keys
        res = {}
        for obj in search_history:
            # Extract all templates
            templates = []
            if isinstance(obj, HasPropertyTemplates):
                for property in obj.properties:
                    templates.append(property[0])
            if isinstance(obj, HasConditionTemplates):
                for condition in obj.conditions:
                    templates.append(condition[0])
            if isinstance(obj, HasParameterTemplates):
                for parameter in obj.parameters:
                    templates.append(parameter[0])

            # Assemble to descriptors
            headers = []
            if mode == AutoConfigureMode.PLAIN:
                headers.append(obj.name)

            for tmpl in templates:
                try:
                    desc = template_to_descriptor(tmpl, headers=headers)
                    res[desc.key] = desc
                except NoEquivalentDescriptorError:
                    continue

        return PlatformVocabulary(entries=res)
