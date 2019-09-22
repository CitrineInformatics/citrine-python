==================
Working With Files
==================

Overview
--------

It is often useful to associate files with your processes, materials, and measurements.
These could be images output by a microscope in a proprietary format, a picture of how several
samples are arranged on a hot plate, or anything else you would like to save.
The association of a file with a resource is done using a
:class:`FileLink <citrine.resources.file_link.FileLink>`,
which is created when you upload a file. The `FileLink` can be associated with runs,
specs, attributes and templates, all of which have a `file_links` field, and it can be used
to download the file.

Uniqueness and Versioning
-------------------------

All FileLink objects are associated with a specific dataset, and they are given a `filename`
when uploaded. The `filename` **must be unique** within the dataset. If you upload another file
with the same `filename` it will be considered a new version of the same file. The old version
is not deleted, but at the moment you can only download the latest version of a given FileLink.

Example
-------

Assume you have a dataset named `dataset` and a file at the location `/Users/me/status_20190913.csv`
on your computer. The code below uploads the file and gives it the filename `microscope_status_20190913.csv`.
It then downloads the file back to your computer at `/Users/me/Downloads/settings.csv`.

.. code-block:: python

    file_link = dataset.files.upload(
        "/Users/me/status_20190913.csv", "microscope_status_20190913.csv")
    dataset.files.download(file_link,
        "/Users/me/Downloads/settings.csv")