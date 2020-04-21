from gemd.entity.template.attribute_template import AttributeTemplate
from gemd.entity.template.base_template import BaseTemplate


def split_templates_from_objects(gems):
    """
    Sort the provided gems into two lists.

    The first list contains only templates (both ObjectTemplate and AttributeTemplate).
    The second list contains only data objects (specs and runs).

    Useful when the procedure for seeding templates needs to be distinct from the procedure for
    seeding data objects.

    Note that each list is unsorted and it is expected that subsequent registration code will
    handle sorting the gems provided.
    """
    templates = []
    data_objects = []
    for gem in gems:
        if isinstance(gem, AttributeTemplate) or isinstance(gem, BaseTemplate):
            templates.append(gem)
        else:
            data_objects.append(gem)
    return templates, data_objects
