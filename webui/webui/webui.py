"""The main Chat app."""

import reflex as rx
import os

from webui import styles
from webui.components import chat, modal, navbar, sidebar
from webui.state import State
from webui.template import path
import shutil

def clear_filepath():
    destination_dir = f"{path}/assets/"

    items_in_directory = os.listdir(destination_dir)

    directories = [item for item in items_in_directory if os.path.isdir(os.path.join(destination_dir, item))]

    for directory in directories:
        dir_path = os.path.join(destination_dir, directory)
        shutil.rmtree(dir_path)



@rx.page(title="RobotAI", on_load=State.check_login)
def index() -> rx.Component:
    clear_filepath()
    """The main app."""
    return rx.vstack(
        navbar(),
        chat.chat(),
        chat.action_bar(),
        sidebar(),
        chat.floating_button(),
        modal(),
        bg=styles.bg_medium_color,
        color=styles.text_light_color,
        min_h="100vh",
        align_items="stretch",
        spacing="0",
    )


# Add state and page to the app.
app = rx.App(style=styles.base_style)
app.add_page(index)
