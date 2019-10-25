Design workflows
================

A design workflow ranks materials according to a :doc:`score <scores>`.
This workflow is comprised of three modules:

-  :doc:`Design space <design_spaces>` defines all possible materials that can be generated.
-  :doc:`Predictor <predictors>` adds information to a material using predictions from a machine-learned model.
-  :doc:`Processor <processors>` defines how to pick the “next” material.

Registration and validation
---------------------------

A workflow is registered with a project and validated before it is ready for use.
Once registered, validation occurs automatically.
Validation status can be one of the following states:

-  **Created:** The module has been registered with a project and has been queued for validation.
-  **Validating:** The workflow is currently validating. The status will be updated to one of the subsequent states upon completion.
-  **Invalid:** Validation completed successfully but found errors with the workflow.
-  **Ready:** Validation completed successfully and found no errors.
-  **Error:** Validation did not complete.
   An error was raised during the validation process that prevented an invalid or ready status to be determined.
   Validation of a workflow and all constituent modules must complete with ready status before the workflow can be executed.

The following example demonstrates how to use the python SDK to register a workflow (assuming a design space, predictor and processor were registered previously), wait for validation to complete and check the final status:

.. code:: python

   from time import sleep
   from citrine import Citrine
   from citrine.informatics.workflows import DesignWorkflow

   # create a session with citrine using API variables
   session = Citrine(API_KEY, API_SCHEME, API_HOST, API_PORT)

   project = session.projects.register('Example project')

   # create a workflow using existing modules and register it with the project
   workflow = project.workflows.register(
       DesignWorkflow(
           name='Example workflow',
           predictor_id=predictor.uid,
           processor_id=processor.uid,
           design_space_id=design_space.uid
       )
   )

   # wait until the workflow is no longer validating
   # we must get the workflow every time we wish to fetch the latest status
   while project.workflows.get(workflow.uid).status == "VALIDATING":
       sleep(10)

   # print final validation status
   validated_workflow = project.workflows.get(workflow.uid)
   print(validated_workflow.status)
   # status info will contain relevant validation information
   # (i.e. why the workflow is valid/invalid)
   print(validated_workflow.status_info)

Execution and results
---------------------

When a design workflow is executed, the processor will search the design space for optimal materials using additional information provided by the predictor.
The result is a list of scored and ranked materials.
Materials at the head of the list are the best materials found from searching the design space.

A workflow can be run using the python SDK.
Triggering a workflow returns a workflow execution object.
A workflow execution has a status (in progress, succeeded, or failed) and results (once execution has succeeded).
Results of a successful workflow are returned as a dictionary.
The ``results`` key maps to a nested list of ``candidates`` and ``scores``.
The ``i``th candidate corresponds to the ``i``th score.

Each candidate and score is a dictionary.
The former contains descriptor key-value pairs and uncertainty in descriptor values.
The latter contains a key-value pair for each score.
For example, if input materials contain an input ``x`` and are scored by using MLI for predicted output ``z`` the execution results would have the form:

.. code:: python

   {
       "results": [
           ["candidates", [
               {"x": 1, "uncertainty_in_x": 0, "z": 2, "uncertainty_in_x": 0.1},
               # ...
           ]],
           ["scores": [
               {"mli_z": 0.8},
               # ...
           ]]
       ]
   }

The length of ``candidates`` will always equal that of ``scores``.
A maximum of 200 candidates and scores can be returned by an execution.
If the design space contains more than 200 possible materials, only the top 200 will be returned by an execution.
Note, the multiple layers of lists in the results.
The ``results`` key maps to a list. This list contains 2 items.
Each item is a list of the form ``[name, [values]]``, e.g. ``["candidates", list_of_candidates]``.

The following demonstrates how to trigger workflow execution, wait for the design run to complete and inspect the best material found by the workflow:

.. code:: python

   from time import sleep
   from citrine.informatics.objectives import ScalarMaxObjective
   from citrine.informatics.scores import MLIScore

   # create a score with the desired objectives and baselines
   score = MLIScore(
       name='Example score',
       description='Used to rank materials',
       # create an objective to maximize shear modulus
       # the descriptor key must match a descriptor in materials produced from teh design space
       objectives=[ScalarMaxObjective(descriptor_key='Shear modulus')],
       baselines=[150.0] # one for each objective
   )

   # trigger a design run using a previously registered and validated workflow
   execution = workflow.executions.trigger(score)

   # wait for execution to complete
   while execution.status().in_progress:
       sleep(10)

   # retrieve the results
   execution_results = execution.results()
   # extract the candidates and the scores
   candidates = execution_results['results'][0][1]
   scores = execution_results['results'][1][1]

   # pull out the candidate with the highest shear modulus and its score
   # (this should be the candidate at the head of the list since we used shear modulus to score and rank materials)
   best_candidate = candidates[0]
   print(best_candidate)
   best_score = scores[0]
   print(best_score)

   # we can confirm the best candidate is at the head of the list using
   # this candidate will be the same as best_candidate above
   candidate_with_max_shear_modulus = max(candidates, key=lambda candidate: float(candidate['Shear modulus']))
   print(candidate_with_max_shear_modulus)
