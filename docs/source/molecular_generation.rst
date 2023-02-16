.. generative_design_execution:

[ALPHA] Generative Design Execution
===================================
The Generative Design Execution tool provided by the Citrine Platform enables the generation of new molecules by making mutations to a set of seed molecules. The user provides information on the selection of molecules and filtering through the use of the :class:`~citrine.informatics.generative_design.GenerativeDesignInput` class. This class is used to define the seed molecules to generate mutations from, the fingerprint type used to calculate the fingerprint similarity, the minimum fingerprint similarity between the seed and the mutated molecule, and the number of initial mutations that will be attempted per seed.

At the end of the generation phase, the mutations are filtered based on their similarity to the starting seed molecules. Mutations that do not meet the similarity threshold (or are duplicates) are discarded. The result is a subset of the original mutations returned as list of :class:`~citrine.informatics.generative_design.GenerativeDesignResult` objects. Like the input, these results contain information about the seed molecule, the mutation, the similarity score, and the fingerprint type used in the execution.

The Citrine Python client provides methods to trigger a generative design execution, wait for the execution to finish `wait_while_executing`, and retrieve the results of the execution. Once you have triggered the execution and waited for it to complete, you can retrieve the results by calling the results() method on the execution object.

The following example shows how to run a generative design execution on the Citrine Platform using the Citrine Python client.

.. code-block:: python

    import os
    from citrine import Citrine
    from citrine.jobs.waiting import wait_while_executing
    from citrine.informatics.generative_design import GenerativeDesignInput, FingerprintType

    session = Citrine(
        api_key=os.environ.get("CITRINE_DEV_API_KEY"),
        scheme="https",
        host=os.environ.get("CITRINE_DEV_HOST"),
        port="443",
    )

    team_uid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    project_uid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    team = session.teams.get(team_uid)
    project = team.projects.get(project_uid)

    # Trigger a new generative design execution
    generative_design_input = GenerativeDesignInput(
        seeds = ["CC(O)=O", "CCCCCCCCCCCC"],
        fingerprint_type = FingerprintType.ECFP4,
        min_fingerprint_similarity = 0.1,
        mutation_per_seed=1000,
    )
    generative_design_execution = project.generative_design_executions.trigger(
        generative_design_input
    )
    execution = wait_while_executing(
        collection=project.generative_design_executions, execution=generative_design_execution
    )
    generated = execution.results()
    mutations = [(gen.seed, gen.mutated) for gen in generated]

    # Or get an execution by ID
    execution_uid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    execution = project.generative_design_executions.get(execution_uid)
    generated = execution.results()
    mutations = [(gen.seed, gen.mutated) for gen in generated]

The execution UID is used to retrieve the `execution` object, and the `results()` method of the `execution` object is used to obtain the mutations.

Candidate results are returned as a list of tuples containing the seed molecule and the mutated molecule.

Notes
-----
To execute the code, you will need to replace the placeholders `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` with valid UIDs from your Citrine environment.

Additionally, make sure that the API key, scheme, host, and port are correctly specified in the `Citrine` initialization.
