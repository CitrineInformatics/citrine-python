Predictor Evaluation Workflows
==============================

A :class:`~citrine.informatics.workflows.predictor_evaluation_workflow.PredictorEvaluationWorkflow` evaluates the performance of a :doc:`Predictor <predictors>`.
Each workflow is composed of one or more :class:`PredictorEvaluators <citrine.informatics.predictor_evaluator.PredictorEvaluator>`.

Predictor evaluators
--------------------

A predictor evaluator defines a method to evaluate a predictor and any relevant configuration, e.g., k-fold cross-validation evaluation that specifies 3 folds.
Minimally, each predictor evaluator specifies a name, a set of predictor responses to evaluate and a set of metrics to compute for each response.
Evaluator names must be unique within a single workflow (more on that `below <#execution-and-results>`__).
Responses are specified as a set of strings, where each string corresponds to a descriptor key of a predictor output.
Metrics are specified as a set of :class:`PredictorEvaluationMetrics <citrine.informatics.predictor_evaluation_metrics.PredictorEvaluationMetric>`.
The evaluator will only compute the subset of metrics valid for each response, so the top-level metrics defined by an evaluator should contain the union of all metrics computed across all responses.

.. _Cross-validation evaluator:
Cross-validation evaluator
^^^^^^^^^^^^^^^^^^^^^^^^^^

A :class:`~citrine.informatics.predictor_evaluator.CrossValidationEvaluator` performs k-fold cross-validation on a predictor.
Cross-validation can only be evaluated on predictors that define training data.
During cross-validation, the predictor's training data is partitioned into k folds.
Each fold acts as the test set once, and the remaining k-1 folds are used as training data.
When the number of folds equals the number of training data points, the analysis is equivalent to leave-one-out cross-validation.
Metrics are computed by comparing the model's predictions to observed values.
Where a metric is computed by taking an average over points in the test folds 
the fold-wise average is reported as opposed to the point-wise average.

We recommend 5 folds and 3 trials as the default.
Decreasing the number of folds makes the cross-validation metrics less accurate, since the training sets are substantially reduced in size.
This can make the model appear to be less accurate than it actually is.
Conversely, increasing the number of folds makes the *uncertainty estimates* for cross-validation metrics less accurate (see warning below).
It makes the uncertainty larger, meaning it is more likely that two models will appear to have equivalent performance when in fact one is better than the other.
Increasing the number of trials results in more accurate cross-validation metrics, but takes longer because more models need to be trained.

This evaluator has an ``ignore_when_grouping`` argument, which can be used to keep similar materials together in a fold and thereby avoid unrealistically optimistic results.
Candidates with different values for ignored keys and identical values for all other predictor inputs will be placed in the same fold.
For example, if you are baking cakes with different ingredients and different oven temperatures and want to group together the data by the ingredients, then
you can set ``ignore_when_grouping={"oven temperature"}``.
That way, two recipes that differ only in their oven temperature will always end up in the same fold.

.. Warning::
    There is no unbiased way to estimate the variance of a metric computed by cross-validation
    (`source <https://www.jmlr.org/papers/volume5/grandvalet04a/grandvalet04a.pdf>`_).
    Citrine Platform uses the bias-corrected fold-wise standard deviation, as this was found to be reasonably accurate, especially when the number of folds is <= 5.
    It is biased-upward, which makes the results more conservative.
    If two models are found to differ significantly in their cross-validation metrics, that difference is likely repeatable.

Predictor evaluation metrics
----------------------------

Predictor evaluation metrics are defined as part of a :class:`~citrine.informatics.predictor_evaluator.PredictorEvaluator`.
For all response types, the metric (:class:`~citrine.informatics.predictor_evaluation_metrics.PVA`) is available to compare predicted versus actual data.
Other available metrics depend on whether the response's type is numeric or categorical.

For numeric responses, the following metrics are available:

  - *Root-mean squared error* (:class:`~citrine.informatics.predictor_evaluation_metrics.RMSE`): square root of the average of the squared prediction error.
    RMSE is a useful and popular statistical metric for model quality.
    RMSE is optimized by least-squares regression.
    It has the same units as the predicted quantity and corresponds to the standard deviation of the residuals not explained by the predictor.
    Lower RMSE means the model is more accurate.
  - *R^2* (:class:`~citrine.informatics.predictor_evaluation_metrics.RSquared`): 1 - (mean squared error / variance of data).
    More precisely known as the "fraction of variance explained," this metric is equal to the coefficient of determination calculated with respect to the line ``predicted = actual``.
    Hence it is commonly referred to as "R^2," but unlike R^2 in the context of linear regression, this metric can be negative.
    Positive values mean that the model captures some of the variation across the training data, and it can be used to drive sequential learning.
    A value of 1.0 indicates a perfect model.
    R^2 is evaluated over all cross-validation folds, hence no uncertainty is calculated for the metric, though the value will vary slightly if cross validation is re-run.
  - *Non-dimensional error* (:class:`~citrine.informatics.predictor_evaluation_metrics.NDME`): RMSE divided by the standard deviation of the observed values in the test set.
    (If training and test set are drawn from the same distribution, the standard deviation of the test set observed values is equivalent to the RMSE of a model that always predicts the mean of the observed values).
    NDME is a useful non-dimensional model quality metric.
    A value of NDME == 0 is a perfect model.
    If NDME == 1, then the model is uninformative.
    Generally, models with NDME < 0.9 can be used in a design workflow.
  - *Standard residual* (:class:`~citrine.informatics.predictor_evaluation_metrics.StandardRMSE`) is the root mean square of standardized errors (prediction errors divided by their predicted uncertainty).
    1.0 is perfectly calibrated.
    Standard residual provides a way to determine whether uncertainty estimates are well-calibrated for this model.
    Residuals are calculated using ``(Predicted - Actual)/(Uncertainty Estimate)``.
    A value below 1 indicates the model is underconfident, i.e. actual values are within predicted error bars, on average.
    A value over 1 indicates the model is overconfident, i.e. actual values fall outside predicted error bars, on average.
  - *Coverage probability* (:class:`~citrine.informatics.predictor_evaluation_metrics.CoverageProbability`) is the fraction of observations for which the magnitude of the error is within a confidence interval of a given coverage level.
    The default coverage level is 0.683, corresponding to one standard deviation.
    The coverage level and coverage probability must both be between 0 and 1.0.
    If the coverage probability is greater than the coverage level then the model is under-confident, and if the coverage probability is less than the coverage level then the model is over-confident.
    While standard residual is weighted towards the outside of the residual distribution (because it looks like a 2-norm), coverage probability gives information about the center of the residual distribution.

For categorical responses, performance metrics include either the area under the receiver operating characteristic (ROC) curve (if there are 2 categories) or the F1 score (if there are > 2 categories).

-  Area under the ROC curve (:class:`~citrine.informatics.predictor_evaluation_metrics.AreaUnderROC`) represents the ability of the model to correctly distinguish samples between two categories.
   If AUC == 1.0, all samples are classified correctly.
   If AUC == 0.5, the model cannot distinguish between the two categories.
   If AUC == 0.0, all samples are classified incorrectly.
-  Support-weighted F1 score (:class:`~citrine.informatics.predictor_evaluation_metrics.F1`) is calculated from averaged precision and recall of the model, weighted by the in-class fraction of true positives according to the formula ``2.0 * precision * recall / (precision + recall) * fraction_true_positives`` summed over each class.
   Scores are bounded by 0 and 1.
   At a value of 1, the model has perfect precision and recall.


.. _execution-and-results:

Execution and results
---------------------

Triggering a Predictor Evaluation Workflow produces a :class:`~citrine.resources.predictor_evaluation_execution.PredictorEvaluationExecution`.
This execution allows you to track the progress using its ``status`` and ``status_info`` properties.
The ``status`` can be one of ``INPROGRESS``, ``READY`` or ``FAILED``.
Information about the execution status, e.g., warnings or reasons for failure, can be accessed via ``status_info``.

When the ``status`` is ``READY``, results for each evaluation defined as part of the workflow can be accessed using the ``results`` method:

.. code:: python

    results = execution.results('evaluator_name')

or by indexing into the execution object directly:

.. code:: python

    results = execution['evaluator_name']

Both methods return a :class:`~citrine.informatics.predictor_evaluation_result.PredictorEvaluationResult`.

Each evaluator defines its own result.
A :class:`~citrine.informatics.predictor_evaluator.CrossValidationEvaluator` returns a :class:`~citrine.informatics.predictor_evaluation_result.CrossValidationResult`, for example.
All predictor evaluation results contain a reference to the evaluator that created the result, the set of responses that were evaluated and the metrics that were computed.

Values associated with computed metrics can be accessed by response key:

.. code:: python

    response_metrics = results['response_key']

This returns a :class:`~citrine.informatics.predictor_evaluation_result.ResponseMetrics` object.
This object contains all metrics that were computed for the ``response_key``.
These metrics can be listed using ``list(response_metrics)``,
and the value associated with a specific metric can be accessed by the metric itself, e.g., ``response_metrics[RMSE()]`` to retrieve the root-mean squared error.

With the exception of predicted vs. actual data, all metric values are returned as a :class:`~citrine.informatics.predictor_evaluation_result.RealMetricValue`.
This object defines properties ``mean`` and ``standard_error``.
The latter optionally returns a float if the evaluation was configured with enough trials allow ``standard_error`` to be computed.
(A :class:`~citrine.informatics.predictor_evaluator.CrossValidationEvaluator` requires at least 3 trials to compute ``standard_error``.)

Predicted vs. actual data (``response_metrics[PVA()]``) is returned as a list of predicted vs. actual data points.
Each data point defines properties ``uuid``, ``identifiers``, ``trial``, ``fold``, ``predicted`` and ``actual``:

 -  ``uuid`` and ``identifiers`` allow you to link a predicted vs. actual data point to the corresponding row in the :ref:`Predictor <predictors>`'s :ref:`Data Source <data-sources>`.
 -  ``trial`` and ``fold`` return the respective index assigned during the evaluation.
 -  The form of ``predicted`` and ``actual`` data depends on whether the response is numeric or categorical.
    For numeric responses, ``predicted`` and ``actual`` return a :class:`~citrine.informatics.predictor_evaluation_result.RealMetricValue` which reports mean and standard error associated the data point.
    For categorical responses, class probabilities are returned as a mapping from each class name (as a string) to its relative frequency (as a float).

Example
-------

The following demonstrates how to create a :class:`~citrine.informatics.predictor_evaluator.CrossValidationEvaluator`, add it to a :class:`~citrine.informatics.workflows.predictor_evaluation_workflow.PredictorEvaluationWorkflow` and use it to evaluate a :class:`~citrine.informatics.predictors.predictor.Predictor`.

The predictor we'll evaluate is defined below:

.. code:: python

    from citrine.informatics.data_sources import CSVDataSource
    from citrine.informatics.descriptors import RealDescriptor
    from citrine.informatics.predictors import SimpleMLPredictor

    x = RealDescriptor(key='x', lower_bound=0.0, upper_bound=1.0, units='')
    y = RealDescriptor(key='y', lower_bound=0.0, upper_bound=1.0, units='')

    data_source = CSVDataSource(
        file_link=file, # path to CSV that contains training data for x and y
        column_definitions={'x': x, 'y': y}
    )

    predictor = SimpleMLPredictor(
        name='y predictor',
        description='predicts y given x',
        inputs=[y],
        outputs=[x],
        latent_variables=[],
        training_data=[data_source]
    )

This predictor expects ``x`` as an input and predicts ``y``.
Training data is provided by a :class:`~citrine.informatics.data_sources.CSVDataSource` that assumes ``filename`` represents the path to a CSV that contains ``x`` and ``y``.

Next, create a project and register the predictor:

.. code:: python

    import os
    from citrine.jobs.waiting import wait_while_validating
    from citrine.seeding.find_or_create import find_or_create_project

    client = Citrine(api_key=os.environ.get('CITRINE_API_KEY'))
    project = find_or_create_project(project_collection=client.projects, project_name='example project')

    predictor = project.predictors.register(predictor)
    wait_while_validating(collection=project.predictors, module=predictor)

In this example we'll create a cross-validation evaluator for the response ``y`` with 8 folds and 3 trials and request metrics for root-mean square error (:class:`~citrine.informatics.predictor_evaluation_metrics.RMSE`) and predicted vs. actual data (:class:`~citrine.informatics.predictor_evaluation_metrics.PVA`).

.. note::
    Here we're performing cross-validation on an output, but latent variables are valid cross-validation responses as well.

.. code:: python

    from citrine.informatics.predictor_evaluator import CrossValidationEvaluator
    from citrine.informatics.predictor_evaluation_metrics import RMSE, PVA

    evaluator = CrossValidationEvaluator(
        name='cv',
        n_folds=8,
        n_trials=3,
        responses={'y'},
        metrics={RMSE(), PVA()}
    )

Then add the evaluator to a :class:`~citrine.informatics.workflows.predictor_evaluation_workflow.PredictorEvaluationWorkflow`, register it with your project and wait for validation to finish:

.. code:: python

    from citrine.informatics.workflows import PredictorEvaluationWorkflow

    workflow = PredictorEvaluationWorkflow(
        name='workflow that evaluates y',
        evaluators=[evaluator]
    )

    workflow = project.predictor_evaluation_workflows.register(workflow)
    wait_while_validating(collection=project.predictor_evaluation_workflows, module=workflow)

Trigger the workflow against a predictor to start an execution.
Then wait for the results to be ready:

.. code:: python

    from citrine.jobs.waiting import wait_while_executing

    execution = workflow.executions.trigger(predictor.uid)
    wait_while_executing(collection=project.predictor_evaluation_executions, execution=execution, print_status_info=True)

Finally, load the results and inspect the metrics and their computed values:

.. code:: python

    # load the results computed by the CV evaluator defined above
    cv_results = execution[evaluator.name]

    # load results for y
    y_results = cv_results['y']

    # listing the results should return the metrics we requested: RMSE and PVA
    computed_metrics = list(y_results)
    print(computed_metrics) # ['rmse', 'predicted_vs_actual']

    # access RMSE and print the mean and standard error
    y_rmse = y_results[RMSE()]
    print(f'RMSE: mean = {y_rmse.mean:0.2f}, standard error = {y_rmse.standard_error:0.2f}')

    # access PVA:
    y_pva = y_results[PVA()]

    print(len(y_pva)) # this should equal the num_trials * num_folds * num_rows
                      # where num_rows == the number of rows in the data source

    # inspect the first data point
    pva_data_point = y_pva[0]

    # print trial and fold indices
    print(pva_data_point.trial) # should be == 1 since trials are 1-indexed,
                                # and this it the first data point
    print(pva_data_point.fold) # should also be == 1

    # inspect predicted and actual values
    predicted = pva_data_point.predicted
    print(f'predicted = {predicted.mean:0.2f} +/- {predicted.standard_error}')
    actual = pva_data_point.actual
    print(f'actual = {actual.mean} +/- {actual.standard_error}')


Archive and restore
-------------------
Both :class:`PredictorEvaluationWorkflows <citrine.informatics.workflows.predictor_evaluation_workflow.PredictorEvaluationWorkflow>` and :class:`PredictorEvaluationExecutions <citrine.resources.predictor_evaluation_execution.PredictorEvaluationExecution>` can be archived and restored.
To archive a workflow:

.. code:: python

    project.predictor_evaluation_workflows.archive(workflow.uid)

and to archive all executions associated with a predictor evaluation workflow:

.. code:: python

    for execution in workflow.executions.list():
        project.predictor_evaluation_executions.archive(execution.uid)

To restore a workflow or execution, simply replace ``archive`` with ``restore`` in the code above.
