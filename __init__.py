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

from . import google_images_download as gid

class CreateCardsDialog(QDialog):
    """Dialog for creating image identification cards."""
    def __init__(self, mw):
        QDialog.__init__(self, parent=mw)
        self.setup_ui()

    def setup_ui(self):
        """Set up widgets on the dialog."""
        layout = QFormLayout()
        layout.addRow(QLabel("Enter search terms, each on its own line:"))

        self.search_terms_input = QPlainTextEdit(self)
        layout.addRow(self.search_terms_input)

        self.search_suffix_input = QLineEdit(self)
        layout.addRow(QLabel("Suffix for every search term, if needed:"),
            self.search_suffix_input)

        self.num_images_input = QSpinBox()
        self.num_images_input.setMinimum(1)
        layout.addRow(QLabel("Number of images for each search term:"),
            self.num_images_input)

        fetch_close_layout = QHBoxLayout()
        self.fetch_button = QPushButton("&Fetch images")
        self.fetch_button.clicked.connect(self.clicked_fetch)
        fetch_close_layout.addWidget(self.fetch_button)
        self.close_button = QPushButton("&Close")
        self.close_button.clicked.connect(self.clicked_close)
        fetch_close_layout.addWidget(self.close_button)
        layout.addRow(fetch_close_layout)

        self.accepted.connect(self.clicked_fetch)
        self.rejected.connect(self.clicked_close)
        self.setLayout(layout)
        self.setMinimumWidth(360)
        self.setWindowTitle('Create image identification cards')
    
    def notify(self, text, icon):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return

    def fetch_single(self, search_term, suffix, num):
        #response = google_images_download.googleimagesdownload(
        #    limit = num,
        #    suffix_keywords = suffix,
        #    keywords = search_term)
        #absolute_image_paths = response.download({<Arguments...>})
        return 1

    def clicked_fetch(self):
        """Fetch the specified images, and create cards."""
        self.setEnabled(False)
        # Get input values
        num = self.num_images_input.value()
        suffix = self.search_suffix_input.text()
        search_terms = self.search_terms_input.document().toPlainText()
        search_terms = search_terms.splitlines()
        search_terms = list(map(lambda s: s.strip(), search_terms))
        search_terms = list(filter(lambda x: x, search_terms))
        if len(search_terms) == 0:
            self.notify("Need at least one nonempty search term!",
                QMessageBox.Critical)
            self.setEnabled(True)
            return
        num_cards_added = 0
        for search_term in search_terms:
            num_cards_added += self.fetch_single(search_term, suffix, num)
        self.notify(f"Successfully added {num_cards_added} cards.",
            QMessageBox.Information)
        self.setEnabled(True)

    def clicked_close(self):
        """Close the image-fetching dialog."""
        self.close()


# Function to be run when user clicks on menu item to run addon
def start_dialog(window):
    dialog = CreateCardsDialog(window)
    dialog.exec_()


# Add menu item
ii_action = QAction("Create &image identification cards", mw)
ii_action.triggered.connect(lambda _, window=mw: start_dialog(window))
mw.form.menuTools.addAction(ii_action)
