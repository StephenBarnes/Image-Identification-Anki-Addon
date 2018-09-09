# -*- coding: utf-8 -*-

"""
Anki addon: Image Identification

This addon allows you to specify a list of search terms. It then automatically
fetches pictures from Google Images matching those search terms, and creates
several cards showing you a picture and asking you to answer with the search
term. We also create one card asking you what the search term looks like, with
all the pictures on the answer side.

License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>

Using the excellent google-images-download program / Python module by Hardik
Vasa; see that module's license in the appropriate subdirectory.

Some code adapted from the Image Occlusion addon by Glutanimate.
"""

import aqt
from aqt.qt import *
from aqt import mw
from aqt.utils import tooltip
from anki.notes import Note

import tempfile

from .google_images_download import google_images_download


# This addon uses 2 models, each with 1 card:
MODEL_1_NAME = "Image Identification, 1 picture"
CARD_1_NAME = "identification, picture -> label"
MODEL_2_NAME = "Image Identification, all pictures"
CARD_2_NAME = "description, label -> pictures"
MODEL_1_FIELDS = ["Label", "Search suffix", "Image(s)"]
MODEL_2_FIELDS = MODEL_1_FIELDS # they're the same
# Define cards' fronts and backs and CSS
CARD_1_FRONT = """\
identify:
<div>{{Image(s)}}</div>\
"""
CARD_1_BACK = """\
{{FrontSide}}
<hr id="answer">
{{Label}}{{#Search suffix}} ({{Search suffix}}){{/Search suffix}}\
"""
CARD_1_CSS = ""
CARD_2_FRONT = """pics: {{Label}}{{#Search suffix}} ({{Search suffix}}){{/Search suffix}}"""
CARD_2_BACK = """\
{{FrontSide}}
<hr id="answer">
<div id="pictures">{{Image(s)}}\
"""
CARD_2_CSS = ""


class CreateCardsDialog(QDialog):
    """Dialog for creating image identification cards."""
    def __init__(self):
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

        self.deck_chooser_widget = QDialog()
        layout.addRow(self.deck_chooser_widget)
        self.deck_chooser = aqt.deckchooser.DeckChooser(mw,
            self.deck_chooser_widget)

        fetch_close_layout = QHBoxLayout()
        self.fetch_button = QPushButton("&Fetch images (please wait)")
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
        """Notify the user of some event."""
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return

    def create_term_cards(self, search_term, paths, suffix, model1, model2):
        """Create all cards for a given search term. Returns number of cards
        created."""
        # Create an image->term card for each image
        img_tags = []
        for temporary_image_path in paths:
            # add to media folder
            permanent_path = mw.col.media.addFile(temporary_image_path)
            img_tag = f'<img src="{permanent_path}" class="image-identification" />'
            img_tags.append(img_tag)
            # create the image -> term card
            note = Note(mw.col, model1)
            note.model()['did'] = self.deck_chooser.selectedId()
            note['Label'] = search_term
            note['Search suffix'] = suffix
            note['Image(s)'] = img_tag
            mw.col.addNote(note)

        # Create term -> all images card
        note = Note(mw.col, model2)
        note.model()['did'] = self.deck_chooser.selectedId()
        note['Label'] = search_term
        note['Search suffix'] = suffix
        note['Image(s)'] = ''.join(img_tags)
        mw.col.addNote(note)

        # Let changes show
        mw.reset()

        return len(img_tags) + 1

    def fetch_term_images(self, search_term, suffix, num):
        """Fetch all images for a single term, and create notes."""
        num_cards_created = 0
        # Create temporary directory for fetched images
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Fetch images
            response = google_images_download.googleimagesdownload()
            arguments = {
                "keywords"          : search_term,
                "limit"             : num,
                "suffix_keywords"   : suffix,
                "output_directory"  : tmpdirname,
                "no_directory"      : True, # place directly in output directory
                }
            image_paths = response.download(arguments)
                # Note: this is a dict from search terms to lists of paths

            # Get the two models we'll use
            model1, model2 = getOrCreateModels()

            for term_paths in image_paths.values(): # should be only one value
                num_cards_created += self.create_term_cards(search_term,
                    term_paths, suffix, model1, model2)

        return num_cards_created

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
        for search_term in search_terms:
            if "," in search_term:
                self.notify("Cannot include commas inside search terms, sorry :(",
                    QMessageBox.Critical)
                self.setEnabled(True)
                return
        
        # Design note: We could only invoke get_google_images once, passing in
        # all search terms together. But that seems like it would cause
        # problems, e.g. with / or \ inside search terms.
        num_cards_added = 0
        for search_term in search_terms:
            num_cards_added += self.fetch_term_images(search_term, suffix, num)

        tooltip(f"Added {num_cards_added} new cards.", parent=self)
        self.setEnabled(True)

    def clicked_close(self):
        """Close the image-fetching dialog."""
        self.close()


def start_dialog():
    """Function to be run when user clicks on menu item to run addon."""
    dialog = CreateCardsDialog()
    dialog.exec_()


def getOrCreateModels():
    """Get the two models used by the addon; if they don't exist yet, create
    them first."""
    model1 = mw.col.models.byName(MODEL_1_NAME)
    if not model1:
        model1 = add_model(MODEL_1_NAME, CARD_1_NAME, MODEL_1_FIELDS,
            CARD_1_FRONT, CARD_1_BACK, CARD_1_CSS)
    model2 = mw.col.models.byName(MODEL_2_NAME)
    if not model2:
        model2 = add_model(MODEL_2_NAME, CARD_2_NAME, MODEL_2_FIELDS,
            CARD_2_FRONT, CARD_2_BACK, CARD_2_CSS)
    return model1, model2


def add_model(model_name, card_name, fields, card_front, card_back, card_css):
    """Add a specific model to the profile's list of models."""
    models = mw.col.models
    my_model = mw.col.models.new(model_name)
    # Add fields:
    for field_name in fields:
        field_obj = models.newField(field_name)
        models.addField(my_model, field_obj)
    # Add template
    template = models.newTemplate(card_name)
    template['qfmt'] = card_front
    template['afmt'] = card_back
    my_model['css'] = card_css
    my_model['sortf'] = 0  # set sort field to label
    models.addTemplate(my_model, template)
    models.add(my_model)
    return my_model

def fname2img(path):
    """Return HTML img element for given path.
    Plagiarized directly from Image Occlusion Enhanced."""
    fname = os.path.split(path)[1]
    return '<img src="%s" />' % fname


# Add menu item
ii_action = QAction("Create &image identification cards", mw)
ii_action.triggered.connect(lambda _, window=mw: start_dialog())
mw.form.menuTools.addAction(ii_action)
