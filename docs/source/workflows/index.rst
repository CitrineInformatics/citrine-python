.. _workflows:

Workflows
=========

The Citrine Platform provides tools to make data-driven decisions for materials research and development using artificial intelligence (AI) workflows.
AI Workflows are composed of modules, which provide the ability to programmatically codify domain knowledge, research capabilities and experimental objectives.
Workflows leverage data and domain knowledge to help materials researchers make traceable, data-driven decisions in pursuit of their research and development goals.
These capabilities include generating candidates for sequential learning, identifying outliers or imputing missing values.

Modules
-------

Modules are re-usable computational tools used to construct workflows.
The modules are dictate how the platform utilizes research data to generate computational results. There are 4 types of modules on the platform:

-  :doc:`Design Spaces <design_spaces>` define the domain of controllable experimental parameters, their allowable values and relevant bounds.
-  :doc:`Predictors <predictors>` define relations between variables in a table of experimental data.
    A predictor can be composed of machine-learned models and (coming soon) analytical relations.
-  :doc:`Processors <processors>` define the method used to search the design space.
   The processor and design space are coupled: depending on the design space used, only a subset of processors are applicable.

Design workflows
----------------

The :doc:`design workflow <design_workflows>` is the core AI workflow on the platform.
This workflow generates scored candidates for sequential learning.
It requires one of each of the modules listed above and executes in the following manner:

-  Material candidates are pulled from the design space.
-  The predictor adds additional information to the candidates.
-  Enriched candidates are scored, and the processor selects the next batch of candidates to pull from the design space.

After a given number of iterations, candidates are ranked according to their score and the best materials are returned.
(Here, the best materials are those that are most likely to optimize an objective and satisfy a set of constraints.)

Workflows are further parameterized by :doc:`Scores <scores>`, which codify experimental objectives, constraints on desired candidates, and strategies for candidate acquisition.

Table of Contents
-----------------

.. toctree::
    :maxdepth: 2

    design_spaces
    predictors
    predictor_reports
    processors
    scores
    design_workflows
