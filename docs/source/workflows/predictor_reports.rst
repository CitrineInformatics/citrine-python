Predictor reports
=================

A predictor report contains information about a machine-learned model and various performance metrics.
The report can be accessed via the python SDK via ``predictor.report``.

A task to generate a predictor report is scheduled when a predictor is registered.
The report has a ``status`` and ``json`` member variables.
Status can be one of:

-  ``PENDING`` The report has been scheduled.
-  ``ERROR`` An error was thrown while generating the report.
-  ``OK`` The report was generated successfully and the results are ready.

Results of the report are stored as a dictionary in the ``json`` member variable.
For the :class:`~citrine.informatics.predictors.SimpleMLPredictor`, this dictionary contains two keys: ``important_features`` and ``performance_metrics``.
Feature importances and performance metrics are computed for each output descriptor.
Important features are the input features that the machine learning model depends on most strongly.
These importances can be useful in gaining some insight into how the machine learning model is making its predictions.

Performance metrics included in the report depend on whether the response is numeric or categorical.
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

An as example, consider a model with ``x`` and ``y`` inputs and a numeric output ``z``.
The following illustrates how to register a predictor, wait for the report to finish and view the results.

.. code:: python

   from time import sleep

   from citrine.informatics.predictors import SimpleMLPredictor

   # create input descriptors
   x = RealDescriptor('x', lower_bound=0, upper_bound=10)
   y = RealDescriptor('y', lower_bound=0, upper_bound=10)
   z = RealDescriptor('z', lower_bound=0, upper_bound=10)

   # register a predictor with a project
   predictor = project.predictors.register(
       SimpleMLPredictor(
           name='ML predictor for z',
           description='Predicts z from x and y',
           inputs=[x, y],
           latent_variables=[],
           outputs=[z],
           training_data='training-data-id'
       )
   )

   # wait for the predictor report to be ready
   while project.predictors.get(predictor.uid).report.status == 'PENDING':
       sleep(10)

   # print the json report
   report = project.predictors.get(predictor.uid).report
   print(report.json)

For this example, the report would resemble the following.
Note, feature importances and performance metrics are keyed on the response (``z``).

.. code:: python

   {
     "important_features": {
       "z": {
         "x": 0.62,
         "y": 0.38
       }
     },
     "performance_metrics": {
       "z": {
         "ndme": {
           "value": 0.39,
           "description": "non-dimensional model error (0.0 for a perfect model)"
         },
         "rmse": {
           "value": 17.40,
           "description": "Root mean squared error (0.0 for a perfect model)"
         },
         "std_residual": {
           "value": 1.18,
           "description": "uncertainty calibration: root mean square of standardized errors (1.0 is perfectly calibrated)"
         },
         "std_confidence": {
           "value": 0.63,
           "description": "uncertainty calibration: fraction of actual values within the prediction error bars (0.68 is perfectly calibrated)"
         }
       }
     }
   }
