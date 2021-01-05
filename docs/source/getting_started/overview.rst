========
Overview
========

The Citrine python client serves as the entry point for creating and interacting with resources on the Citrine Platform.
There are a few basic types of resources to become acquainted with: projects, datasets, data objects, and AI modules.
A project is a container for a thematically related group of datasets and AI modules that a specific group of people have access to.
A dataset contains a related set of data objects: information about materials samples, the way they were processed, and the measurements performed on them.
A dataset can also contain files related to these data objects.
AI modules are used to construct workflows that analyze materials data and make predictions to help inform data-driven materials development.

In this first section we will cover projects, datasets, and the basic mechanics of creating, reading, updating, and deleting resources.
We will also briefly describe data objects and AI modules.
For more information on uploading and working with data objects, see :doc:`this section <../data_entry>`.
A thorough explanation of the various AI modules and how to use them can be found :doc:`here <../workflows/getting_started>`.
Finally, documentation on how to extract information about data objects and express it in a tabular format so it can be consumed by AI modulesis found :doc:`here <../data_extraction>`.