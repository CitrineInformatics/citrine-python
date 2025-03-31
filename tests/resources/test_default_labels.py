import pytest

from citrine.resources._default_labels import _inject_default_label_tags

@pytest.mark.parametrize(
    "original_tags, default_labels, expected",
    [
        (None, None, None),
        (None, [], []),
        ([], None, []),
        ([], [], []),
        (
            None,
            ["label 0", "label 1"],
            ["citr_auto::mat_label::label 0", "citr_auto::mat_label::label 1"],
        ),
        (
            [],
            ["label 0", "label 1"],
            ["citr_auto::mat_label::label 0", "citr_auto::mat_label::label 1"],
        ),
        (["alpha", "beta", "gamma"], None, ["alpha", "beta", "gamma"]),
        (["alpha", "beta", "gamma"], [], ["alpha", "beta", "gamma"]),
        (
            ["alpha", "beta", "gamma"],
            ["label 0", "label 1"],
            [
                "alpha",
                "beta",
                "gamma",
                "citr_auto::mat_label::label 0",
                "citr_auto::mat_label::label 1",
            ],
        ),
    ],
)
def test_inject_default_label_tags(original_tags, default_labels, expected):
    result = _inject_default_label_tags(original_tags, default_labels)
    assert result == expected
