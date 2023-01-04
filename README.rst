AFM software list
=================
|Check Status| |Build Status|

This repository is used for managing the
`AFM software list <https://afm-spm.github.io/afm-software-list/>`_.


Contributing
------------
If you would like to add a software to this list, you have two options:

1. Use the `issue template for new entries <https://github.com/AFM-SPM/afm-software-list/issues/new?assignees=paulmueller&labels=entries&template=new-software-list-entry.md&title=Please+add+this+software%3A+NAME>`_.
   This template contains a form with all the column headers in the software list.

2. Make a pull-request. Fork this repository and run
   ``python afm-list-manager.py add-entry`` (see below for instructions).
   This will create a new .json file in the ``entries`` directory which
   you can then add to your pull request.


List management
---------------
The ``afm-list-manager.py`` Python script manages the software list,
which includes tasks such as:

- adding entries
- adding keywords
- consistency checks

First install the Python dependencies:

::

    pip install -r requirements.txt

To see a list of available commands and options, run

::

    python afm-list-manager.py --help


.. |Check Status| image:: https://img.shields.io/github/actions/workflow/status/AFM-SPM/afm-software-list/check.yml%20list%20entries?label=List-Checks
   :target: https://github.com/AFM-SPM/afm-software-list/actions?query=workflow%3A%22Check+list+entries%22

.. |Build Status| image:: https://img.shields.io/github/actions/workflow/status/AFM-SPM/afm-software-list/check.yml%20software%20list%20to%20gh-pages?label=HTML-build
   :target: https://github.com/AFM-SPM/afm-software-list/actions?query=workflow%3A%22Publish+software+list+to+gh-pages%22
