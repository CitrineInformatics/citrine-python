Performance workflows
=====================

A performance workflow runs cross-validation analysis on a predictor configuration.

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

When a performance workflow is executed then the cross-validation analysis will be performed against the given `predictor` and will contain performance metrics
for the `output` descriptor in your `predictor`.

A workflow can be run using the python SDK.

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
     'results': [
       [
         'report', {
           'performance_metrics': {
             '~~z': {
               'ndme': {'value': 0.4777230639684575, 'description': 'Non-dimensional model error (0.0 for a perfect model)'},
               'rmse': {'value': 21.307943307393984, 'description': 'Root mean squared error (0.0 for a perfect model)'},
               'std_residual': {'value': 1.8288119041155286, 'description': 'Uncertainty calibration: root mean square of standardized errors (1.0 is perfectly calibrated)'},
               'std_confidence': {'value': 0.59375, 'description': 'Uncertainty calibration: fraction of actual values within the prediction error bars (0.68 is perfectly calibrated)'}
             }
           }
         }
       ]
     ]
   }
