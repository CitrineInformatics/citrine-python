.. generative_design_execution:

[ALPHA] Generative Design Execution
===================================
The Citrine Platform offers a Generative Design Execution tool that allows the creation of new molecules by applying mutations to a set of given seed molecules.
To use this feature, you need to provide a set of starting molecules and filtering parameters using the :class:`~citrine.informatics.generative_design.GenerativeDesignInput` class.

The class requires you to define the seed molecules for generating mutations, the fingerprint type used to calculate the `fingerprint similarity <https://www.rdkit.org/docs/GettingStartedInPython.html#fingerprinting-and-molecular-similarity>`_, the minimum fingerprint similarity between the seed and mutated molecule, and the number of initial mutations attempted per seed.

Various fingerprint types are available on the Citrine Platform, including Atom Pairs (AP), Path-Length Connectivity (PHCO), Binary Path (BPF), Paths of Atoms of Heteroatoms (PATH), Extended Connectivity Fingerprint with radius 4 (ECFP4) and radius 6 (ECFP6), and Focused Connectivity Fingerprint with radius 4 (FCFP4) and radius 6 (FCFP6).
Each fingerprint type captures different aspects of molecular structure and influences the generated mutations.
You can access these fingerprint types through the :class:`~citrine.informatics.generative_design.FingerprintType` enum, like `FingerprintType.ECFP4`.

After the generative design process is complete, the mutations are filtered based on their similarity to the starting seed molecules.
Mutations that do not meet the similarity threshold or are duplicates will be discarded. The remaining mutations are returned as a subset of the original mutations in the form of a list of :class:`~citrine.informatics.generative_design.GenerativeDesignResult` objects.
These results contain information about the seed molecule, the mutation, the similarity score, and the fingerprint type used during execution.

After triggering the execution and waiting for completion, the user can retrieve the results and utilize them in their work.'
The following example demonstrates how to run a generative design execution on the Citrine Platform using the Citrine Python client.

.. code-block:: python

    import os
    from citrine import Citrine
    from citrine.jobs.waiting import wait_while_executing
    from citrine.informatics.generative_design import GenerativeDesignInput, FingerprintType

    session = Citrine(
        api_key=os.environ.get("API_KEY"),
        scheme="https",
        host=os.environ.get("CITRINE_HOST"),
        port="443",
    )

    team_uid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    project_uid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    team = session.teams.get(team_uid)
    project = team.projects.get(project_uid)

    # Trigger a new generative design execution
    generative_design_input = GenerativeDesignInput(
        seeds=["CC(O)=O", "CCCCCCCCCCCC"],
        fingerprint_type=FingerprintType.ECFP4,
        min_fingerprint_similarity=0.1,
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

    # Or get a completed execution by ID
    execution_uid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    execution = project.generative_design_executions.get(execution_uid)
    generated = execution.results()
    mutations = [(gen.seed, gen.mutated) for gen in generated]

To execute the code, replace the `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` placeholders with valid UIDs from your Citrine environment. Ensure that the API key, scheme, host, and port are correctly specified in the `Citrine` initialization.