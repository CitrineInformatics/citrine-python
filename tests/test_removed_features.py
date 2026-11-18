"""Removed platform features warn on import and fail on use, with the platform's own message."""

import importlib
import re
import subprocess
import sys
import uuid
import warnings

import pytest
from packaging.version import Version

from citrine.__version__ import __version__
from citrine._utils.removed_features import REMOVED_IN
from citrine.exceptions import CitrineException, FeatureRemovedError
from citrine.informatics.design_spaces import ProductDesignSpace
from citrine.resources.project import Project
from tests.utils.session import FakeSession

GENERATIVE_DESIGN_REMOVED = "Generative design has been removed from the Citrine Platform."
SAMPLING_REMOVED = "Design space sampling has been removed from the Citrine Platform."

# Each (module, name) pair that a released version of citrine-python let a script import.
REMOVED_IMPORTS = [
    ("citrine.informatics.generative_design", "GenerativeDesignInput", GENERATIVE_DESIGN_REMOVED),
    ("citrine.informatics.generative_design", "GenerativeDesignResult", GENERATIVE_DESIGN_REMOVED),
    ("citrine.informatics.generative_design", "FingerprintType", GENERATIVE_DESIGN_REMOVED),
    ("citrine.informatics.generative_design", "StructureExclusion", GENERATIVE_DESIGN_REMOVED),
    ("citrine.informatics.executions", "GenerativeDesignExecution", GENERATIVE_DESIGN_REMOVED),
    ("citrine.informatics.executions", "GenerativeDesignResult", GENERATIVE_DESIGN_REMOVED),
    (
        "citrine.informatics.executions.generative_design_execution",
        "GenerativeDesignExecution",
        GENERATIVE_DESIGN_REMOVED,
    ),
    (
        "citrine.informatics.executions.generative_design_execution",
        "GenerativeDesignResult",
        GENERATIVE_DESIGN_REMOVED,
    ),
    (
        "citrine.resources.generative_design_execution",
        "GenerativeDesignExecutionCollection",
        GENERATIVE_DESIGN_REMOVED,
    ),
    (
        "citrine.resources.generative_design_execution",
        "GenerativeDesignExecution",
        GENERATIVE_DESIGN_REMOVED,
    ),
    (
        "citrine.resources.generative_design_execution",
        "GenerativeDesignInput",
        GENERATIVE_DESIGN_REMOVED,
    ),
    (
        "citrine.informatics.design_spaces.sample_design_space",
        "SampleDesignSpaceInput",
        SAMPLING_REMOVED,
    ),
    ("citrine.informatics.design_candidate", "SampleSearchSpaceResultCandidate", SAMPLING_REMOVED),
    (
        "citrine.informatics.executions.sample_design_space_execution",
        "SampleDesignSpaceExecution",
        SAMPLING_REMOVED,
    ),
    (
        "citrine.informatics.executions.sample_design_space_execution",
        "SampleSearchSpaceResultCandidate",
        SAMPLING_REMOVED,
    ),
    (
        "citrine.resources.sample_design_space_execution",
        "SampleDesignSpaceExecutionCollection",
        SAMPLING_REMOVED,
    ),
    (
        "citrine.resources.sample_design_space_execution",
        "SampleDesignSpaceExecution",
        SAMPLING_REMOVED,
    ),
    (
        "citrine.resources.sample_design_space_execution",
        "SampleDesignSpaceInput",
        SAMPLING_REMOVED,
    ),
]

REMOVED_ENUMERATIONS = {"FingerprintType", "StructureExclusion"}

REMOVED_CLASSES = [entry for entry in REMOVED_IMPORTS if entry[1] not in REMOVED_ENUMERATIONS]


def raises_removed(message: str):
    return pytest.raises(FeatureRemovedError, match=f"^{re.escape(message)}$")


def import_removed(module_name: str, name: str):
    """Import a removed name, and suppress the warning that tests below assert on."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return getattr(importlib.import_module(module_name), name)


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project(session) -> Project:
    project = Project(name="Removed features", session=session, team_id=uuid.uuid4())
    project.uid = uuid.uuid4()
    return project


@pytest.fixture
def design_space(session, project) -> ProductDesignSpace:
    design_space = ProductDesignSpace(name="Removed features", description="")
    design_space.uid = uuid.uuid4()
    design_space._project_id = project.uid
    design_space._session = session
    return design_space


def test_removal_error_is_a_citrine_exception():
    assert issubclass(FeatureRemovedError, CitrineException)
    assert issubclass(FeatureRemovedError, AttributeError)


@pytest.mark.parametrize("module_name, name, message", REMOVED_IMPORTS)
def test_importing_a_removed_name_warns(module_name, name, message):
    expected = (
        f"{module_name}.{name} is deprecated as of 5.4.0 and will be removed in 6.0.0. {message}"
    )
    with pytest.warns(DeprecationWarning, match=f"^{re.escape(expected)}$") as record:
        exec(f"from {module_name} import {name}", {})
    # The warning names the importing code, so Python shows it by default in a script.
    assert record[0].filename == "<string>"


@pytest.mark.parametrize("module_name, name, message", REMOVED_CLASSES)
def test_constructing_a_removed_class_raises(module_name, name, message):
    removed_class = import_removed(module_name, name)
    with raises_removed(message):
        removed_class()
    with raises_removed(message):
        removed_class(seeds=["C"], n_candidates=50)


@pytest.mark.parametrize("module_name, name, message", REMOVED_CLASSES)
def test_calling_a_method_of_a_removed_class_raises(module_name, name, message):
    removed_class = import_removed(module_name, name)
    for method in ("build", "trigger", "list", "get", "results"):
        with raises_removed(message):
            getattr(removed_class, method)


def test_removed_classes_answer_introspection():
    removed_class = import_removed(
        "citrine.informatics.generative_design", "GenerativeDesignInput"
    )
    assert not hasattr(removed_class, "__wrapped__")
    assert isinstance(object(), removed_class) is False


def test_removed_enumerations_keep_their_members():
    fingerprint_type = import_removed("citrine.informatics.generative_design", "FingerprintType")
    exclusion = import_removed("citrine.informatics.generative_design", "StructureExclusion")
    assert fingerprint_type.ECFP4.value == "ECFP4"
    assert exclusion.IONS.value == "IONS"


def test_the_same_class_comes_from_every_module():
    from_informatics = import_removed(
        "citrine.informatics.executions", "GenerativeDesignExecution"
    )
    from_resources = import_removed(
        "citrine.resources.generative_design_execution", "GenerativeDesignExecution"
    )
    assert from_informatics is from_resources


def test_unknown_names_raise_without_a_warning():
    module = importlib.import_module("citrine.informatics.generative_design")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(AttributeError, match="has no attribute 'NoSuchName'"):
            module.NoSuchName
        exec("from citrine.informatics.executions import *", {})


def test_importing_citrine_emits_no_removal_warning():
    script = (
        "import warnings\n"
        "warnings.simplefilter('always')\n"
        "with warnings.catch_warnings(record=True) as record:\n"
        "    import citrine\n"
        "    import citrine.informatics.executions\n"
        "    import citrine.informatics.design_candidate\n"
        "    import citrine.informatics.generative_design\n"
        "    import citrine.informatics.design_spaces.sample_design_space\n"
        "    import citrine.informatics.executions.generative_design_execution\n"
        "    import citrine.informatics.executions.sample_design_space_execution\n"
        "    import citrine.resources.generative_design_execution\n"
        "    import citrine.resources.sample_design_space_execution\n"
        "print(sum('removed from the Citrine Platform' in str(w.message) for w in record))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "0"


def test_generative_design_executions_raise(project, session):
    with raises_removed(GENERATIVE_DESIGN_REMOVED):
        project.generative_design_executions.list()
    assert session.num_calls == 0


def test_sample_design_space_executions_raise(design_space, session):
    with raises_removed(SAMPLING_REMOVED):
        design_space.sample_design_space_executions.trigger(None)
    assert session.num_calls == 0


def test_removed_accessors_are_absent_to_introspection(project, design_space, session):
    assert not hasattr(project, "generative_design_executions")
    assert not hasattr(design_space, "sample_design_space_executions")
    assert session.num_calls == 0


def test_removed_names_are_gone_by_version_6():
    assert Version(__version__) < Version(REMOVED_IN), (
        f"Version {REMOVED_IN} removes generative design and design space sampling. "
        "Delete citrine._utils.removed_features, the modules that import it, "
        "FeatureRemovedError's accessors, and this test file."
    )
