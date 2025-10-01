==================================
Migrating to Predictor Evaluations
==================================

Summary
=======

In version 4.0, :py:class:`Predictor Evaluation Workflows <citrine.resources.predictor_evaluation_workflow.PredictorEvaluationWorkflowCollection>` and :py:class:`Predictor Evaluation Executions <citrine.resources.predictor_evaluation_execution.PredictorEvaluationExecutionCollection>` (collectively, PEWs) will be merged into a single entity called :py:class:`Predictor Evaluations  <citrine.resources.predictor_evaluation.PredictorEvaluationCollection>`. The new entity will retain the functionality of its predecessors, while simplyfing interactions with it. And it will support the continuing evolution of the platform.

Basic Usage
===========

The most common pattern for interacting with PEWs is executing the default evaluators and waiting for the result:

.. code:: python

    pew = project.predictor_evaluation_workflows.create_default(predictor_id=predictor.uid)
    execution = next(pew.executions.list(), None)
    execution = wait_while_executing(collection=project.predictor_evaluation_executions, execution=execution)

With Predictor Evaluations, it's more straight-forward:

.. code:: python

    evaluation = project.predictor_evaluations.trigger_default(predictor_id=predictor.uid)
    evaluation = wait_while_executing(collection=project.predictor_evaluations, execution=evaluation)

The evaluators used are available with :py:meth:`~citrine.informatics.executions.predictor_evaluation.PredictorEvaluation.evaluators`.

Working With Evaluators
=======================

You can still construct evaluators (such as :class:`~~citrine.informatics.predictor_evaluator.CrossValidationEvaluator`) the same way as you always have, and run them against your predictor:

.. code:: python

    evaluation = project.predictor_evaluations.trigger(predictor_id=predictor.uid, evaluators=evaluators)

If you don't wish to construct evaluators by hand, you can retrieve the default one(s):

.. code:: python

    evaluators = project.predictor_evaluations.default(predictor_id=predictor.uid)

You can evaluate your predictor even if it hasn't been registered to the platform yet:

.. code:: python

    evaluators = project.predictor_evaluations.default_from_config(predictor)

Once evaluation is complete, the results will be available by calling :py:meth:`~citrine.informatics.executions.predictor_evaluation.PredictorEvaluation.results` with the name of the desired evaluator (which are all available through :py:meth:`~citrine.informatics.executions.predictor_evaluation.PredictorEvaluation.evaluator_names`).
