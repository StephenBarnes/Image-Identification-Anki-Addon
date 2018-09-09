# -*- coding: utf-8 -*-

"""
Anki addon: Image Identification

This addon allows you to specify a list of search terms. It then automatically
fetches pictures from Google Images matching those search terms, and creates
several cards showing you a picture and asking you to answer with the search
term. We also create one card asking you what the search term looks like, with
all the pictures on the answer side.

License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>
"""

import aqt
from aqt.qt import *
from aqt import mw

try:
    import google_images_import as gii
except ImportError:
    gii = None

# Define the main options dialog


def start_dialog(window):
    if gii is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("You must install the google_images_import to use "
                "the Image Identification add-on. Please run this command in "
                "a terminal, then restart Anki:")
            msg.setInformativeText("pip install google_images_import")
            msg.setWindowTitle("Image Identification addon")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return


# Add menu item
ii_action = QAction("Create &image identification cards", mw)
ii_action.triggered.connect(lambda _, window=mw: start_dialog(window))
    # note that this modifies both our `config` and the one stored in the mw.col.conf['udarnik']
mw.form.menuTools.addAction(ii_action)
