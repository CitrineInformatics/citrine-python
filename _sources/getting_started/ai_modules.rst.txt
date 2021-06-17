==================
AI Engine Overview
==================

Overview
--------

The Citrine Platform uses artificial intelligence (AI) to accelerate your materials research and development.
The platform exposes several types of Modules -- re-usable assets that codify domain knowledge, research capabilities, or experimental objectives.
Modules are combined into Workflows that provide actionable information to help direct research and development.

The Citrine Python client allows you to create and manipulate Modules and Workflows.
Workflows can be executed and the results inspected.
This page provides the briefest of overviews; for a more thorough discussion see the :doc:`AI Engine documentation <../workflows/getting_started>`.

Modules
-------

Predictors
^^^^^^^^^^

:doc:`Predictors <../workflows/predictors>` define relations between variables.
Predictors can be machine learning models, analytic relations, or featurizers.
Several Predictors can be combined into a graphical model that expresses your domain knowledge and predicts material properties with quantified uncertainty estimates.

Design Spaces
^^^^^^^^^^^^^

:doc:`Design Spaces <../workflows/design_spaces>` define the set of materials of interest.

Processors
^^^^^^^^^^

:doc:`Processors <../workflows/processors>` define the method used to search a Design Space.

Workflows
---------

Design Workflow
^^^^^^^^^^^^^^^

:doc:`Design Workflows <../workflows/design_workflows>` generate proposals for materials that are expected to meet some goal.
A Design Workflow combines a Design Space to define to materials of interest, a Predictor to predict material properties, and a Processor to explore the space.
They also include a :doc:`Score <../workflows/scores>` which codifies goals of the project.

Predictor Evaluation Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:doc:`Predictor Evaluation Workflows <../workflows/predictor_evaluation_workflows>` analyze the quality of a Predictor.
