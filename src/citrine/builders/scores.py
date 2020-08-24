from typing import List

from citrine.informatics.constraints import Constraint, ScalarRangeConstraint
from citrine.informatics.objectives import Objective, ScalarMinObjective
from citrine.informatics.scores import Score, LIScore


def pareto_scores(
        name: str,
        objectives: List[Objective],
        constraints: List[Constraint],
        baselines: List[List[float]]
) -> List[Score]:
    if len(objectives) != 2:
        raise ValueError("pareto_scores only supports 2 objectives")
    if any(len(x) != 2 for x in baselines):
        raise ValueError("some baselines don't contain two values")

    x_key = objectives[0].descriptor_key
    y_key = objectives[1].descriptor_key
    min_x = isinstance(objectives[0], ScalarMinObjective)
    min_y = isinstance(objectives[0], ScalarMinObjective)

    sorted_baselines = sorted(baselines, key=lambda x: x[0])

    scores = []
    for i in range(len(sorted_baselines)):
        additional_constraints = []
        if min_x:
            if i > 0:
                last_y = sorted_baselines[i-1][1]
                if min_y:
                    constraint = ScalarRangeConstraint(descriptor_key=y_key, max=last_y)
                else:
                    constraint = ScalarRangeConstraint(descriptor_key=y_key, min=last_y)
                additional_constraints.append(constraint)
            if i < len(sorted_baselines) - 1:
                next_x = sorted_baselines[i+1][0]
                constraint = ScalarRangeConstraint(descriptor_key=x_key, max=next_x)
                additional_constraints.append(constraint)
        else:
            if i > 0:
                last_x = sorted_baselines[i-1][0]
                constraint = ScalarRangeConstraint(descriptor_key=x_key, min=last_x)
                additional_constraints.append(constraint)
            if i < len(sorted_baselines) - 1:
                next_y = sorted_baselines[i+1][1]
                if min_y:
                    constraint = ScalarRangeConstraint(descriptor_key=y_key, max=next_y)
                else:
                    constraint = ScalarRangeConstraint(descriptor_key=y_key, min=next_y)
                additional_constraints.append(constraint)

        x_base, y_base = sorted_baselines[i]

        scores.append(LIScore(
            name="{} beyond ({}, {})".format(name, x_base, y_base),
            objectives=objectives,
            constraints=constraints + additional_constraints,
            baselines=sorted_baselines[i]
        ))

    return scores
