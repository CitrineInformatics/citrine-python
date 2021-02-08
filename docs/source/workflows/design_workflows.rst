[ALPHA] Design Workflows
========================

A design workflow ranks materials according to a :doc:`score <scores>`.
This workflow is comprised of three modules:

-  :doc:`Design space <design_spaces>` defines all possible materials that can be generated.
-  :doc:`Predictor <predictors>` adds information to a material using predictions from a machine-learned model.
-  :doc:`Processor <processors>` defines how to pick the “next” material.

The following example demonstrates how to use the python SDK to register a workflow (assuming a design space, predictor and processor were registered previously), wait for validation to complete and check the final status:

.. code:: python

    from time import sleep
    from citrine.informatics.workflows import DesignWorkflow

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

Using the new flow, the process is very similar, but uses the `design_workflow` resource:

.. code:: python

    from citrine.informatics.workflows import DesignWorkflow
    from citrine.jobs.waiting import wait_while_validating

    # create a workflow using existing modules and register it with the project
    workflow = project.design_workflows.register(
        DesignWorkflow(
            name='Example workflow',
            predictor_id=predictor.uid,
            processor_id=processor.uid,
            design_space_id=design_space.uid
        )
    )

    # wait until the workflow is no longer validating
    wait_while_validating(project.design_workflows, workflow, print_status_info=True)

    # print final validation status
    validated_workflow = project.design_workflows.get(workflow.uid)
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
The ``results`` key maps to a dictionary containing ``candidates`` and ``scores``.
The ``i`` th candidate corresponds to the ``i`` th score.

Each candidate and score is a dictionary.
The former contains descriptor key-value pairs and uncertainty in descriptor values.
The latter contains a key-value pair for each score.

For example, if input materials contain an input ``x`` and are scored by using LI for predicted output ``z`` the execution results would have the form:

.. code:: python

    {
        "results": {
            "candidates": [
                {"x": 1, "uncertainty_in_x": 0, "z": 2, "uncertainty_in_x": 0.1},
                # ...
            ],
            "scores": [
                {"li_z": 0.8},
                # ...
            ]
        }
    }

The length of ``candidates`` will always equal that of ``scores``.
A maximum of 200 candidates and scores can be returned by an execution.
If the design space contains more than 200 possible materials, only the top 200 will be returned by an execution.

The following demonstrates how to trigger workflow execution, wait for the design run to complete and inspect the best material found by the workflow:

.. code:: python

    from time import sleep
    from citrine.informatics.objectives import ScalarMaxObjective
    from citrine.informatics.scores import LIScore


    # create a score with the desired objectives and baselines
    score = LIScore(
        # create an objective to maximize shear modulus
        # the descriptor key must match a descriptor in materials produced from teh design space
        objectives=[ScalarMaxObjective(descriptor_key='Shear modulus')],
        baselines=[150.0] # one for each objective
    )

    # trigger a design run using a previously registered and validated workflow
    execution = workflow.executions.trigger(score)

    # wait for execution to complete
    wait_while_executing(execution, print_status_info=True, collection=workflow.design_executions)

    # retrieve the results
    execution_results = execution.results()
    # extract the candidates and the scores
    candidates = execution_results['results']['candidates']
    scores = execution_results['results']['scores']

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


In the updated design execution workflow, results are paginated and returned as :class:`~citrine.informatics.design_candidate.DesignCandidate` objects.

.. code:: python

    from citrine.informatics.objectives import ScalarMaxObjective
    from citrine.informatics.scores import LIScore
    from citrine.jobs.waiting import wait_while_executing


    # create a score with the desired objectives and baselines
    score = LIScore(
        # create an objective to maximize shear modulus
        # the descriptor key must match a descriptor in materials produced from teh design space
        objectives=[ScalarMaxObjective(descriptor_key='Shear modulus')],
        baselines=[150.0] # one for each objective
    )

    # trigger a design run using a previously registered and validated workflow
    execution = workflow.design_executions.trigger(score)

    # wait for execution to complete
    wait_while_executing(execution, print_status_info=True, collection=workflow.design_executions)

    # get the candidate generator
    execution_results = execution.candidates()

    # pull out the candidate with the highest shear modulus and its score
    # (this should be the candidate at the head of the list since we used shear modulus to score and rank materials)
    # Note that because execution_results is a generator, calling this multiple times will iterate through the generator, getting the next best candidate
    best_candidate = execution_results.send(None)
    print(best_candidate)
    best_score = best_candidate.primary_score
    print(best_score)

    # Alternatively, you can iterate over the candidates generator, looking at each candidate
    for candidate in execution.candidates():
        print(candidate.primary_score)

    # To save all candidates in memory in one list:
    all_candidates = list(execution.candidates())

    # we can confirm the best candidate is at the head of the list using
    # this candidate will be the same as best_candidate above
    candidate_with_max_shear_modulus = max(all_candidates, key=lambda candidate: candidate.material.values['Shear modulus'].mean)
    print(candidate_with_max_shear_modulus)

Design Candidates
-----------------

A :class:`~citrine.informatics.design_candidate.DesignCandidate` represents the result of the Design Execution. They contain the `primary score` of the candidate and the :class:`~citrine.informatics.design_candidate.DesignMaterial` for that candidate. DesignMaterials are simpler approximations ("projections") of the materials information about a particular design candidate.

DesignMaterials approximate the distribution of values the variable might take. They may be one of:
    * :class:`~citrine.informatics.design_candidate.MeanAndStd`
    * :class:`~citrine.informatics.design_candidate.TopCategories`
    * :class:`~citrine.informatics.design_candidate.Mixture`
    * :class:`~citrine.informatics.design_candidate.ChemicalFormula`
    * :class:`~citrine.informatics.design_candidate.MolecularStructure`.

For example:

.. code:: python

    candidate = execution.candidates().send(None)

    # to get the score of a particular candidate
    score = candidate.primary_score

    # A MeanAndStd material will have mean and std
    candidate.material.values['mean_and_std_material'].mean
    candidate.material.values['mean_and_std_material'].std

    # A TopCategories material will have the probability map for the most probable categories
    candidate.material.values['top_categories_material'].probabilities

    # A Mixture material will have the most likely quantity values for all of the components in a mixture
    candidate.material.values['mixture_material'].quantities

    # A ChemicalFormula material will have the chemical formula as a string
    candidate.material.values['chemical_formula_material'].formula

    # A MolecularStructure material will have the molecular structure represented by the SMILE string
    candidate.material.values['molecular_material'].smiles
