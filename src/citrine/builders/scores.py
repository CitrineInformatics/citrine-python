import csv
from io import StringIO
from typing import List, Iterable

from citrine.resources.project import Project
from citrine.resources.gemtables import GemTable

from citrine.informatics.objectives import Objective, ScalarMinObjective
from citrine.informatics.scores import Score, LIScore


def create_default_score(
    *, objectives: List[Objective], project: Project, table: GemTable
) -> Score:
    """[ALPHA] Create a default score from the provided objectives.

    Reads the provided table from S3 storage,
    and parses the columns corresponding to each objective's descriptor key
    to extract relevant baseline values.

    The baselines are determined as the min/max of the column data,
    depending on whether the objective is a ScalarMinObjective or ScalarMaxObjective.

    Parameters
    ----------
    objectives: List[Objective]
        List of objectives to include in a score.
    project: Project
        Project to use when accessing the Citrine Platform.
    table: GemTable
        Table to read baseline data from.
        Must contain column definitions matching the descriptor keys
        found in each objective.

    Returns
    ----------
    Score
        The default constructed score.
        Currently, this is a LIScore containing containing all provided objectives.

    """
    table_data = project.tables.read_to_memory(table)
    data_io = StringIO(table_data)
    reader = csv.DictReader(data_io, delimiter=",")

    objectives = objectives if isinstance(objectives, Iterable) else [objectives]

    header_map = {}
    objective_values = {}
    for objective in objectives:
        key = objective.descriptor_key
        objective_values[key] = []

        # Descriptor key has to be mapped to fieldnames of table data
        # Search for mean column, avoid matching on std columns
        full_key = next(filter(lambda col: f"{key}~Mean" in col, reader.fieldnames), None)
        if full_key is None:
            raise ValueError(f"Key '{key}' not found in GEM table headers.")
        header_map[key] = full_key

    # Iterate table data to extract baseline info
    for row in reader:
        for objective in objectives:
            key = objective.descriptor_key
            full_key = header_map[key]
            try:
                objective_values[key].append(float(row[full_key]))
            except ValueError:
                continue

    # Determine max/min of extracted values for baseline
    baselines = []
    for objective in objectives:
        key = objective.descriptor_key
        if len(objective_values[key]) == 0:
            raise ValueError(f"Unable to parse values for '{key}' as numeric.")

        comparator = min if isinstance(objective, ScalarMinObjective) else max
        baselines.append(comparator(objective_values[key]))

    score = LIScore(objectives=objectives, baselines=baselines)
    return score
