from typing import List, Optional

from citrine.resources.data_concepts import CITRINE_TAG_PREFIX

_CITRINE_DEFAULT_LABEL_PREFIX = f"{CITRINE_TAG_PREFIX}::mat_label"


def _inject_default_label_tags(
    original_tags: Optional[List[str]], default_labels: Optional[List[str]]
) -> Optional[List[str]]:
    if default_labels is None:
        all_tags = original_tags
    else:
        labels_as_tags = [
            f"{_CITRINE_DEFAULT_LABEL_PREFIX}::{label}" for label in default_labels
        ]
        if original_tags is None:
            all_tags = labels_as_tags
        else:
            all_tags = list(original_tags) + labels_as_tags
    return all_tags
