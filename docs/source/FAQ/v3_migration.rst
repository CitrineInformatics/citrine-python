================
Migrating to 3.0
================

Summary
=======

The newest major release of citrine-python cleans accumulated deprecations as we evolve the Citrine
platform. The intent is to focus users as we aim to reduce confusion by providing a single way to
accomplish each of your tasks.

Keep in mind that you can keep using 2.x until you're ready to upgrade. But until you do, you won't
get any new features or bug fixes.

Goals
-----

The intent of this guide is not to itemize every piece of code removed. The easiest way to
determine what you'll need to change is to upgrade citrine to the latest 2.x release (2.42.2), run
your scripts, and take note of the deprecation warnings. Whenever possible, those warnings will
direct you on how to modify your code such that it will continue to function as desired upon
upgrading to citrine-python 3.x.

This guide seeks to give a high-level overview of those changes, naming some of the categories of
elements no longer supported and what action to take, as well as some of the more consequential
individual changes.

Versions / Runtimes
===================

The following library versions and Python versions are no longer supported.

Versions < 2.26.1
-----------------

The citrine-python SDK is a client for the Citrine platform. As such, we will occasionally need to
make upgrades to the platform which will break old versions of the SDK.

At some point after the release of 3.0, we will be making platform upgrades which will change the
way clients must interact with Search Spaces. So if you're using any version of citrine prior to
2.26.1 (released on June 28, 2023), and you're interacting with Search Spaces (e.g. through
:py:attr:`project.design_spaces <citrine.resources.project.Project.design_spaces>`), your code will
break. Please upgrade to the latest 2.x release, or to 3.0, to avoid this issue. If this poses any
problems for you, please notify your customer contact so we can work with you.

Python 3.7
----------

Official upstream support for Python 3.7 by the Python Software Foundation ended in June 2023. As
such, we no longer support its use, and may begin using language features which are not backwards
compatable with it. Upgrade to at least Python 3.8, keeping in mind
`their migration guide <https://docs.python.org/3.8/whatsnew/3.8.html>`_.

Features
========

The following features are no longer supported.

Branch ID
---------

Previously, branch references were inconsistent. Some used a unique "branch ID", and others the
"root ID". This was further complicated by the web app only ever showing the "root ID". The reason
has to do with the platform implementation, but resulted in a confusing user experience.

Beginning in 3.0, that "branch ID" is hidden from users. Instead, the SDK will always present the
branch's root ID and version, akin to
:py:class:`Predictor <citrine.informatics.predictors.graph_predictor.GraphPredictor>` ID and
version. To access branches, you'll just use that root ID, and optionally the version: omitting the
version will grab the most recent version, which will almost always be what you want.

status_info
-----------

We have completed moving all our assets which previously used :code:`status_info` (such as but not
limited to :py:class:`~citrine.informatics.predictors.predictor.Predictor` and
:py:class:`~citrine.informatics.workflows.design_workflow.DesignWorkflow`) to use
:code:`status_detail`. These objects contain richer information, such as log level and (optionally)
error codes, along with the message.

DesignSpace.archive and DesignSpace.restore
-------------------------------------------

In the past, archiving a Search Space required updating it, which carried the risk of accidental
modification. Since 2.26.1, we've supported a separate
:py:meth:`~citrine.resources.design_space.DesignSpaceCollection.archive` and 
:py:meth:`~citrine.resources.design_space.DesignSpaceCollection.restore` call. So we no longer
support archiving via :py:meth:`~citrine.resources.design_space.DesignSpaceCollection.update`.

citrine.builders
----------------

This package contained a handful of utilities which were by all accounts unused, and better suited
to live outside citrine-python, anyways.

formulation_descriptor parameters
---------------------------------

In many cases, the Citrine platform will generate an appropriate formulation descriptor on your
behalf. For example, when creating a
:py:class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor` or
:py:class:`~citrine.informatics.data_sources.GemTableDataSource`. In such cases, you can no longer
specify a formulation descriptor.

:py:attr:`project.modules <citrine.resources.project.ProjectCollection.modules>`
--------------------------------------------------------------------------------

This was the remnant of the old Citrine platform, before we began to specialize our assets. For
over a year, it has only returned Search Spaces, for which you should be using
:py:meth:`project.design_spaces <citrine.resources.project.ProjectCollection.design_spaces>`. As
such, both it and :code:`citrine.resources.modules` were dropped.

Dehydrated Search Spaces
------------------------

This is a feature from the early days of the platform. It hasn't been supported for quite some time
due to lack of use and complexity of support. But mechanisms for it were still present in
citrine-python, allowing users to specify subspaces by ID. Fully dropping support completes its
removal.

Process File Protocol
---------------------

This refers to the old method of getting data on the platform using :code:`Dataset.files.process`.
It's been supplanted by :py:meth:`~citrine.resources.file_link.FileCollection.ingest`, rendering
:code:`process` and the whole :code:`citrine.resources.job` module irrelevant.

convert_to_graph and convert_and_update
---------------------------------------

:code:`SimpleMLPredictor` was a very old type of AI Model which hasn't been supported by the
platform in a long time. As such, these methods to convert them into the equivalent
:py:class:`~citrine.informatics.predictors.graph_predictor.GraphPredictor` are no longer needed. If
you think you still use a :code:`SimpleMLPredictor`, please reach out to your customer contact so we can
work with you to convert it.

:py:meth:`~citrine.seeding.find_or_create.find_or_create_project` requires a team ID
------------------------------------------------------------------------------------

In mid-2022, the platform introduced teams, which are collections of projects. As such, starting
with 3.0, :py:meth:`~citrine.seeding.find_or_create.find_or_create_project` can only operate on a
:py:class:`~citrine.resources.project.ProjectCollection` which includes a team ID. That is, instead
of passing :py:attr:`citrine.projects <citrine.citrine.Citrine.projects>`, you most likely want to
pass :py:attr:`team.projects <citrine.resources.team.Team.projects>`.

Ingredient Ratio Constraint bases are now sets
----------------------------------------------

They were initially implemented as Python dictionaries to allow for flexibility. But as we evolved
their usage on the platform, we found we only needed the list of ingredients/labels. To allow
migration while preserving the old behavior, we added
:py:meth:`~citrine.informatics.constraints.ingredient_ratio_constraint.IngredientRatioConstraint.basis_ingredient_names`
and
:py:meth:`~citrine.informatics.constraints.ingredient_ratio_constraint.IngredientRatioConstraint.basis_label_names`.
Note that
once you've upgraded to 3.0, you'll be prompted to move back to
:py:meth:`~citrine.informatics.constraints.ingredient_ratio_constraint.IngredientRatioConstraint.basis_ingredients` and
:py:meth:`~citrine.informatics.constraints.ingredient_ratio_constraint.IngredientRatioConstraint.basis_labels`.
