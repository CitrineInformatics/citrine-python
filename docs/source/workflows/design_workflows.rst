Design Workflows
========================

A :class:`~citrine.informatics.workflows.design_workflow.DesignWorkflow` ranks materials according to a :doc:`score <scores>`.
This workflow is comprised of two modules:

-  :doc:`Design space <design_spaces>` defines all possible materials that can be generated.
-  :doc:`Predictor <predictors>` adds information to a material using predictions from a machine-learned model.

The following example demonstrates how to use the Citrine Python client to register a workflow (assuming a design space and predictor were registered previously), wait for validation to complete and check the final status:

.. code:: python

    from citrine.informatics.workflows import DesignWorkflow
    from citrine.jobs.waiting import wait_while_validating

    # create a workflow using existing modules and register it with the project
    workflow = project.design_workflows.register(
        DesignWorkflow(
            name='Example workflow',
            predictor_id=predictor.uid,
            predictor_version=predictor.version,
            design_space_id=design_space.uid
        )
    )

    # wait until the workflow is no longer validating
    wait_while_validating(collection=project.design_workflows, module=workflow, print_status_info=True)

    # print final validation status
    validated_workflow = project.design_workflows.get(workflow.uid)
    print(validated_workflow.status)
    # status info will contain relevant validation information
    # (i.e. why the workflow is valid/invalid)
    print(validated_workflow.status_info)


Execution and results
---------------------

When a design workflow is executed, the Citrine Platform will search the design space for optimal materials using additional information provided by the predictor.
The result is a list of scored and ranked materials.
Materials at the head of the list are the best materials found from searching the design space.

A workflow can be run using the Citrine Python client.
Triggering a workflow returns a workflow execution object.
A workflow execution has a status (in progress, succeeded, or failed) and results (once execution has succeeded).

Candidate results are paginated and returned as `DesignCandidate <#design-candidate>`__ objects.

.. code:: python

    from citrine.informatics.objectives import ScalarMaxObjective
    from citrine.informatics.scores import LIScore
    from citrine.jobs.waiting import wait_while_executing


    # create a score with the desired objectives and baselines
    score = LIScore(
        # create an objective to maximize shear modulus
        # the descriptor key must match a descriptor in materials produced from the design space
        objectives=[ScalarMaxObjective(descriptor_key='Shear modulus')],
        baselines=[150.0] # one for each objective
    )

    # trigger a design run using a previously registered and validated workflow
    execution = workflow.design_executions.trigger(score)

    # wait for execution to complete
    wait_while_executing(collection=workflow.design_executions, execution=execution, print_status_info=True)

    # get the candidate generator
    execution_results = execution.candidates()

    # pull out the candidate with the highest shear modulus and its score
    # (this should be the candidate at the head of the list since we used shear modulus to score and rank materials)
    # Note that because execution_results is a generator, calling this multiple times will iterate through the generator, getting the next best candidate
    best_candidate = next(execution_results)
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


You can to look up what :doc:`score <scores>` was used for a particular execution, as well as which :doc:`descriptors <descriptors>` where used:

.. code:: python

    score = execution.score
    descriptors = execution.descriptors


.. _design_candidate_anchor:

Design Candidate
-----------------

A :class:`~citrine.informatics.design_candidate.DesignCandidate` represents the result of the Design Execution.
They contain the `primary score` of the candidate and the :class:`~citrine.informatics.design_candidate.DesignMaterial` for that candidate.
DesignMaterials are simpler approximations ("projections") of the materials information about a particular design candidate.

DesignMaterials approximate the distribution of values that a variable might take.
Each variable is represented as one of:

* :class:`~citrine.informatics.design_candidate.MeanAndStd`
* :class:`~citrine.informatics.design_candidate.TopCategories`
* :class:`~citrine.informatics.design_candidate.Mixture`
* :class:`~citrine.informatics.design_candidate.ChemicalFormula`
* :class:`~citrine.informatics.design_candidate.MolecularStructure`.

For example:

.. code:: python

    candidate = next(execution.candidates())

    # to get the score of a particular candidate
    score = candidate.primary_score

    # Assume a real descriptor, 'elastic limit', represented as a MeanAndStd variable
    candidate.material.values['elastic limit'].mean
    candidate.material.values['elastic limit'].std

    # Assume a categorical descriptor, 'color', represented as a TopCategories variable
    candidate.material.values['color'].probabilities

    # Assume a formulation descriptor, 'Flat Formulation', represented as a Mixture variable
    candidate.material.values['Flat Formulation'].quantities

    # Assume a chemical formula descriptor, 'alloying material', represented as a ChemicalFormula variable
    candidate.material.values['alloying material'].formula

    # Assume a molecular structure descriptor, 'solvent', represented as a MolecularStructure variable
    candidate.material.values['solvent'].smiles

Branches
--------

Branches are purely an organizational concept, used to group design workflows with similar goals under a single name.
They are the primary organizational concept of AI assets as displayed in our web UI.
In the context of the Citrine Python client, they can be thought of as a bucket of design workflows.
If you do not wish to interact with them in the python client, ignore the ``branch_id`` on a DesignWorkflow, and it will be handled for you.

A branch has a name, along with any number of design workflows.
A DesignWorkflow can be created and retrieved, and you can list all design workflows on a branch.
You can still list all design workflows on the project as before.

.. code:: python

    from citrine.informatics.workflows import DesignWorkflow
    from citrine.jobs.waiting import wait_while_validating
    from citrine.resources import Branch

    # create a branch to hold a new design workflow
    branch = project.branches.register(Branch(name='example branch'))

    # create a workflow using existing modules and register it with the project
    workflow = branch.design_workflows.register(
        DesignWorkflow(
            name='Example workflow',
            predictor_id=predictor.uid,
            predictor_version=predictor.version,
            design_space_id=design_space.uid
        )
    )

    # wait until the workflow is no longer validating
    wait_while_validating(collection=branch.design_workflows, module=workflow, print_status_info=True)

    # print final validation status
    validated_workflow = branch.design_workflows.get(workflow.uid)
    print(validated_workflow.status)
    # status info will contain relevant validation information
    # (i.e. why the workflow is valid/invalid)
    print(validated_workflow.status_info)


When you're done with a branch, it can be archived, removing it from the results of ``list`` and setting the ``archived`` flag.
``list_archived`` lists all archived branches in a project. An archived branch can be restored via its unique ID.

Note that archiving branches is independent of archiving the design workflows contained within it.
Archiving a branch will hide the entire branch from default displays in the web UI.
As a result, the design workflows it contained within it will also be hidden.
Yet archiving th branch will *not* change the archived status of the contained design workflows in the context of design workflow listing methods.

Similarly, archiving a design workflow will result in its executions and relevant assets no longer being displayed within the branch.
Thus, archiving all the design workflows contained within a branch will result in a hidden branch on the web UI, but the archival status of the branch will not change.

.. code:: python

    # Display whether your branch is archived.
    print(my_branch.archived)

    # Archive the branch, hiding it from view.
    my_branch = project.branches.archive(my_branch.uid)  # my_branch.archived == True

    # List only the branches in this project which have been archived.
    for branch in project.branches.list_archived():
        print(branch.uid)

    # Restore the branch to active status.
    my_branch = project.branches.restore(my_branch.uid)  # my_branch.archived == False

You can also update the data on a branch similarly to the web application by using the ``update_data`` method on a :class:`~citrine.resources.branch.BranchCollection` with the desired arguments:

.. code:: python

    # Update the data on my_branch
    my_updated_branch = project.branches.update_data(branch=my_branch)
