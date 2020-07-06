Performance workflows
=====================

A :class:`performance workflow <citrine.informatics.workflows.PerformanceWorkflow>` performs analysis on a module.
Running a performance workflow produces a report (currently in JSON format) that describes the results of the analysis.
Each analysis computes one or more performance metrics, e.g. accuracy of an ML predictor.
An analysis is codified by a configuration object that stores all relevant settings and parameters required to run the workflow.
By storing the configuration, the object captures domain-specific knowledge used to characterize a module.
With this information we know what settings were used in past analyses and can run the same analysis again in the future.
For example, we might reuse an analysis to compute a specific metric across a range of modules (to determine which module is best suited for our application) or to record the same analysis for a range of different module settings.

Cross-validation analysis
-------------------------

A :class:`~citrine.informatics.analysis_configuration.CrossValidationAnalysisConfiguration` performs cross-validation on a predictor.
This analysis configuration defines cross-validation parameters such as the number of folds, group-by keys (descriptor keys used to group and deduplicate candidates across folds) and others.

The following example demonstrates how to use the Python SDK to register a performance workflow, wait for validation to complete and check the final status:

.. code:: python

   from time import sleep
   from citrine.informatics.workflows import PerformanceWorkflow
   from citrine.informatics.analysis_configuration import CrossValidationAnalysisConfiguration

   workflow = project.workflows.register(
       PerformanceWorkflow(
           name='Demo Performance Workflow',
           analysis=CrossValidationAnalysisConfiguration(
               name='analysis_settings',
               description='2-fold cross-validation',
               n_folds=2,
               n_trials=3,
               max_rows=200,
               seed=10,
               group_by_keys=['~~x']
           )
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

When a performance workflow is executed against a module, it performs an analysis and returns performance metrics in the form of a dictionary.
For a cross-validation analysis, cross-validation is performed against the supplied predictor: the predictor's training data are partitioned into several folds, and each fold takes a turn acting as the test set.
For each test set, the rest of the data are used to train the predictor, and the ensuing model is applied to the held-out test set.
By comparing the model's predictions to the observed values, we can compute several performance metrics that provide information about model quality.
For numeric responses, the available performance metrics are as follows:

  - *Root-mean squared error* (RMSE): square root of the average of the squared prediction error.
    RMSE is a useful and popular statistical metric for model quality.
    RMSE is optimized by least-squares regression, and in that sense is the most "natural" measure for it; it has the same units as the predicted quantity, and corresponds to the standard deviation of the variance not explained by the predictor.
    Lower RMSE means the model is more accurate.
  - *Non-dimensional error* (NDME): RMSE divided by the standard deviation of the observed values in the test set.
    (If training and test set are drawn from the same distribution, the standard deviation of the test set observed values is equivalent to the RMSE of a model that always predicts the mean of the observed values).
    NDME is a useful non-dimensional model quality metric.
    A value of NDME = 0 is a perfect model.
    If NDME = 1, then the model is uninformative.
    An acceptable NDE depends on how the model is used.
    Generally, NDME > 0.9 indicates a model with low accuracy.
    If 0.9 > NDME > 0.6, this model is typically a good candidate for a design workflow.
    Lower values of NDE indicate increasingly accurate models.
  - *Standard residual* is the root mean square of standardized errors (prediction errors divided by their predicted uncertainty).
    1.0 is perfectly calibrated.
    Standard residual provides a way to determine whether uncertainty estimates are well-calibrated for this model.
    Residuals are calculated using ``(Predicted - Actual)/(Uncertainty Estimate)``.
    A value below 1 indicates the model is underconfident, i.e. actual values are within predicted error bars, on average.
    A value over 1 indicates the model is overconfident, i.e. actual values fall outside predicted error bars, on average.
  - *Coverage probability* is the fraction of observations for which the magnitude of the error is within a confidence interval of a given coverage level.
    The default coverage level is 0.683, corresponding to one standard deviation.
    The coverage level and coverage probability must both be between 0 and 1.0.
    If the coverage probability is greater than the coverage level then the model is under-confident, and if the coverage probability is less than the coverage level then the model is over-confident.
    While standard residual is weighted towards the outside of the residual distribution (because it looks like a 2-norm), coverage probability gives information about the center of the residual distribution.

For categorical responses, performance metrics include either the area under the receiver operating characteristic (ROC) curve (if there are 2 categories) or the F1 score (if there are > 2 categories).

-  Area under the ROC curve (AUC) represents the ability of the model to correctly distinguish samples between two categories.
   If AUC=1.0, all samples are classified correctly.
   If AUC=0.5, the model cannot distinguish between the two categories.
   If AUC=0.0, all samples are classified incorrectly.
-  Support-weighted F1 score is calculated from averaged precision and recall of the model, weighted by the in-class fraction of true positives according to the formula ``2.0 * precision * recall / (precision + recall) * fraction_true_positives`` summed over each class.
   Scores are bounded by 0 and 1. At a value of 1, the model has perfect precision and recall.

In addition to the aforementioned metrics, predicted vs. actual data are also available.
The structure of the data will depend on whether the response is numeric or categorical.
For numeric responses, predicted and actual data contain the value and standard error associated with each data point.
For categorical responses, class probabilities are returned.
(If desired, a precision-based metric for categorical responses can be computed using the equation ``1 / max(class_probability) - 1``.)

The following demonstrates how to trigger workflow execution using an already existing ``predictor`` and the ``workflow`` created in the example above.:

.. code:: python

   from time import sleep
   from citrine.informatics.modules import ModuleRef

   execution = workflow.executions.trigger(ModuleRef(str(predictor.uid)))
   # wait for the execution to complete
   while execution.status().in_progress:
       sleep(10)
   execution_results = execution.results()

Triggering a workflow returns a workflow execution object.
A workflow execution has a status (in progress, succeeded, or failed) and results (once execution has succeeded).
Results of a successful workflow are returned as a dictionary.
Below shows an example of the results object.

.. code:: python

   {
       'cross-validation analysis': {
           'results': {
               '~~z': {
                   'ndme': {'value': 0.478, 'standard_error': 0.1},
                   'rmse': {'value': 21.3, 'standard_error': 1.0},
                   'std_residual': {'value': 1.83, 'standard_error': 0.2},
                   'coverage_prob': {'level': 0.683, 'value': 0.594, 'standard_error': 0.03},
                   'predicted_vs_actual': [
                       {
                           'uuid': 'cbe7d566-6370-4e35-a007-29ca369189cf',
                           'predicted': {'value': 0.25, 'standard_error': 0.01},
                           'actual': {'value': 0.25, 'standard_error': 0.01}
                       },
                       {
                           'uuid': 'c31ff865-1a49-4738-8221-ab62feace9d5',
                           'predicted': {'value': 0.33, 'standard_error': 0.14},
                           'actual': {'value': 0.33, 'standard_error': 0.14}
                       }
                   ]
               }
           }
       }
   }

The top level key is the name of the analysis and contains ``results`` for each predictor response, in this case ``~~z``.
If other responses were present in the predictor, their descriptor keys would be present as peers to ``~~z``, and the value would map to a dictionary that contains performance metrics computed for the response.

The previous example outlined the response for a numeric response.
As outlined above, predicted vs. actual data for a categorical response include predicted and actual class probabilities.
If there was a second categorical response ``~~y`` with 2 categories, the response would resemble:

.. code:: python

   {
       'cross-validation analysis': {
           'results': {
               '~~z': {
                   'ndme': {'value': 0.478, 'standard_error': 0.1},
                   'rmse': {'value': 21.3, 'standard_error': 1.0},
                   'std_residual': {'value': 1.83, 'standard_error': 0.2},
                   'coverage_prob': {'level': 0.683, 'value': 0.594, 'standard_error': 0.03},
                   'predicted_vs_actual': [
                       {
                           'uuid': 'cbe7d566-6370-4e35-a007-29ca369189cf',
                           'predicted': {'value': 0.25, 'standard_error': 0.01},
                           'actual': {'value': 0.25, 'standard_error': 0.01}
                       },
                       {
                           'uuid': 'c31ff865-1a49-4738-8221-ab62feace9d5',
                           'predicted': {'value': 0.33, 'standard_error': 0.14},
                           'actual': {'value': 0.33, 'standard_error': 0.14}
                       }
                   ]
               },
               '~~y': {
                   # Note, AUC is present (instead of F1 score)
                   # because there are only 2 categories
                   'auc': {'value': 0.9, 'standard_error': 0.05},
                   'predicted_vs_actual': [
                       {
                           'uuid': 'cbe7d566-6370-4e35-a007-29ca369189cf',
                           'predicted': {'class_1': 0.8, 'class_2': 0.2},
                           'actual': {'class_1': 1.0, 'class_2': 0.0}
                       },
                       {
                           'uuid': 'c31ff865-1a49-4738-8221-ab62feace9d5',
                           'predicted': {'class_1': 0.1, 'class_2': 0.9},
                           'actual': {'class_1': 0.0, 'class_2': 1.0}
                       }
                   ]
               }
           }
       }
   }


