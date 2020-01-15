Performance workflows
=====================

A :class:`performance workflow <citrine.informatics.workflows.PerformanceWorkflow>` performs analysis on a module.
On construction, a performance workflow requires a configuration object which stores all settings required to run the analysis.
Currently, the only implemented analysis performs cross-validation on a predictor.
Settings used to perform cross-validation are defined by a :class:`~citrine.informatics.analysis_configuration.CrossValidationAnalysisConfiguration`.
This analysis configuration defines cross-validation parameters such as the number of folds, group-by keys (descriptor keys used to group and deduplicate candidates across folds) and :class:`others <citrine.informatics.analysis_configuration.CrossValidationAnalysisConfiguration>`.

The following example demonstrates how to use the python SDK to register a performance workflow, wait for validation to complete and check the final status:

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

When a performance workflow is executed against a module, it performs the analysis and returns an "analysis results" dictionary that contains performance metrics.
For a cross-validation analysis, cross-validation is performed against the supplied predictor: the predictor's training data are partitioned into several "folds," and each fold takes a turn acting as the "test set."
For each test set, the rest of the data are used to train the predictor, and the ensuing model is applied to the held-out test set.
By comparing the model's predictions to the true values, we can compute several performance metrics that provide information about model quality.

- Root-mean squared error (RMSE): the square root of the average of the squared prediction error
- Non-dimensional model error (NDME): The RMSE, normalized by the RMSE of a trivial model that always predicts the mean value of the data.
- Standard residual: The RMSE of the standardized error (the prediction error divided by the prediction uncertainty)
- Standard confidence: The fraction of predictions for which the prediction error is less than the prediction uncertainty

Performance metrics included in the results depend on whether the response is numeric or categorical.
For numeric responses, performance metrics include root mean squared error (RMSE), non-dimensional error (NDE), standard residual and standard confidence.

-  RMSE is a useful and popular statistical metric for model quality.
   Lower RMSE means the model is more accurate.
-  NDE is the ratio between RMSE and standard deviation of the output variable.
   NDE is a useful non-dimensional model quality metric.
   A value of NDE = 0 is a perfect model. If NDE = 1, then the model is uninformative.
   An acceptable NDE depends on how the model is used.
   Generally, NDE > 0.9 indicates a model with very high uncertainty.
   If 0.9 > NDE > 0.6, this model is typically a good candidate for a design workflow.
   Lower values of NDE indicate increasingly accurate models.
-  Standard residual is the root mean square of standardized errors.
   (1.0 is perfectly calibrated.)
   Standard residual provides a way to determine whether uncertainty estimates are well-calibrated for this model.
   Residuals are calculated using ``(Predicted - Actual)/(Uncertainty Estimate)``.
   A value below 1 indicates the model is underconfident, i.e. actual values are within predicted error bars, on average.
   A value over 1 indicates the model is overconfident, i.e. actual values fall outside predicted error bars, on average.
-  Standard confidence is the fraction of actual values within the predicted error bars.
   (0.68 is perfectly calibrated.)

For categorical responses, performance metrics include either the area under the receiver operating characteristic (ROC) curve (if there are 2 categories) or the F1 score (if there are > 2 categories).

-  Area under the ROC curve (AUC) represents the ability of the model to correctly distinguish samples between two categories.
   If AUC=1.0, all samples are classified correctly.
   If AUC=0.5, the model cannot distinguish between the two categories.
   If AUC=0.0, all samples are classified incorrectly.
-  F1 score is calculated from precision and recall of the model, weighted by the number of true positives according to the formula ``2.0 * precision * recall / (precision + recall) * true_positives``.
   Scores are bounded by 0 and 1. At a value of 1, the model has perfect precision and recall.

The following demonstrates how to trigger workflow execution using an already existing `predictor` object and the `workflow` created in the example above.:

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
    'results': {
      'performance_metrics': {
        '~~z': {
          'ndme': {'value': 0.4777230639684575, 'description': 'Non-dimensional model error (0.0 for a perfect model)'},
          'rmse': {'value': 21.307943307393984, 'description': 'Root mean squared error (0.0 for a perfect model)'},
          'std_residual': {'value': 1.8288119041155286, 'description': 'Uncertainty calibration: root mean square of standardized errors (1.0 is perfectly calibrated)'},
          'std_confidence': {'value': 0.59375, 'description': 'Uncertainty calibration: fraction of actual values within the prediction error bars (0.68 is perfectly calibrated)'}
        }
      }
    }
  }
