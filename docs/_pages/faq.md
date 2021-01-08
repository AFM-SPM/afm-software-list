---
permalink: faq/
layout:    page
title:     FAQ
---

**How can I add a new entry to the AFM software list?**

The list is maintained in the [AFM-SPM/afm-software-list](https://github.com/AFM-SPM/afm-software-list/)
Github repository. You have two options to add a new entry:

1. Use the [issue template for new entries](https://github.com/AFM-SPM/afm-software-list/issues/new?assignees=paulmueller&labels=entries&template=new-software-list-entry.md&title=Please+add+this+software%3A+NAME).
   This template contains a form with all the column headers in the software list.

2. Make a pull-request. Fork the repository and run the following code:
   ```
   pip install -r requirements.txt
   python afm-list-manager.py add-entry
   ```
   You will be asked a few questions after which a new .json file is
   created in the ``entries`` directory. Add this file to your pull request.
