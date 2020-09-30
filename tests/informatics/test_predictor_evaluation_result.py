"""Tests for citrine.informatics.descriptors."""
import json
import pytest
from citrine.informatics.predictor_evaluation_metrics import *
from citrine.informatics.predictor_evaluation_result import PredictorEvaluationResult


def test_deser_result(example_result_dict):
    example_result = PredictorEvaluationResult.build(example_result_dict)
