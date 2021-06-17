.. _getting-started:

Getting Started
===============

The Citrine Platform provides tools to make data-driven decisions for materials research and development using artificial intelligence (AI) workflows.
AI Workflows are composed of modules, which provide the ability to programmatically codify domain knowledge, research capabilities, and experimental objectives.
Workflows leverage data and domain knowledge to help materials researchers make traceable, data-driven decisions in pursuit of their research and development goals.
These capabilities include generating candidates for Sequential Learning, identifying outliers, or imputing missing values.

Workflows Overview
------------------

Currently, there are two workflows on the AI Engine: the :doc:`DesignWorkflow <design_workflows>` and the :doc:`PredictorEvaluationWorkflow <predictor_evaluation_workflows>`.
Workflows employ reusable modules in order to execute.
There are three different types of modules, and these are discussed in greater detail below.

Design Workflow
***************

The :doc:`DesignWorkflow <design_workflows>` is the core AI workflow on the platform.
This workflow generates scored candidates for Sequential Learning.
It requires one of each of the modules listed below and executes in the following manner:

-  Material candidates are pulled from the design space.
-  The predictor adds additional information to the candidates.
-  Enriched candidates are scored, and the processor selects the next batch of candidates to pull from the design space.

After a given number of iterations, candidates are ranked according to their score and the best materials are returned.
(Here, the best materials are those that are most likely to optimize an objective and satisfy a set of constraints.)

Design workflows are further parameterized by :doc:`Scores <scores>`, which codify experimental objectives and constraints on desired candidates, and define the strategy for candidate acquisition.

Predictor Evaluation Workflow
*****************************

The :doc:`PredictorEvaluationWorkflow <predictor_evaluation_workflows>` is used to analyze a :doc:`Predictor <predictors>`.
This workflow helps users understand how well their predictor module works with their data: in essence, it describes the trustworthiness of their model.
These outcomes are captured in a series of response metrics.

Modules Overview
----------------

Modules are re-usable computational tools used to construct workflows.
The modules dictate how the platform utilizes research data to generate computational results.
There are 3 types of modules on the platform:

-  :doc:`Design Spaces <design_spaces>` define the domain of controllable experimental parameters, their allowable values and relevant bounds.
-  :doc:`Predictors <predictors>` define relations between variables in a table of experimental data.
    A predictor can be composed of machine-learned models, featurizers, and analytical relations.
-  :doc:`Processors <processors>` define the method used to search the design space.
   The processor and design space are coupled: depending on the design space used, only a subset of processors are applicable.

.. _archiving_label:

Archiving
*********

Modules and workflows start active by default when created.
An archived resource will not show up when listing, and an archived module cannot be used in workflows.
To archive a resource with a known ``uid``, use the ``.archive()`` method of the relevant collection
(e.g., :meth:`DesignWorkflowCollection.archive() <citrine.resources.design_workflow.DesignWorkflowCollection.archive>`).
Use ``.restore()`` to un-archive the resource.

Registration and validation
---------------------------

Both modules and workflows are registered with a project and validated before they are ready for use. Once registered, validation occurs automatically.
Validation status can be one of the following states:

-  **Created:** The module/workflow has been registered with a project and has been queued for validation.
-  **Validating:** The module/workflow is currently validating. The status will be updated to one of the subsequent states upon completion.
-  **Invalid:** Validation completed successfully but found errors with the workflow/module.
-  **Ready:** Validation completed successfully and found no errors.
-  **Error:** Validation did not complete. An error was raised during the validation process that prevented an invalid or ready status to be determined.

Validation of a workflow and all constituent modules must complete with ready status before the workflow can be executed.

Experimental functionality
**************************

Both modules and workflows can be used to access experimental functionality on the platform.
In some cases, the module or workflow type itself may be experimental.
In other cases, whether a module or workflow represents experimental functionality may depend on the specific configuration of the module or workflow.
For example, a module might have an experimental option that is turned off by default.
Another example could be a workflow that contains an experimental module.
Because the experimental status of a module or workflow may not be known at registration time, it is computed as part
of the validation process and then returned via two fields:

- `experimental` is a Boolean field that is true when the module or workflow is experimental
- `experimental_reasons` is a list of strings that describe what about the module or workflow makes it experimental
