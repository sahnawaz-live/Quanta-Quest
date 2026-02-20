"""Quanta Quest - An educational quantum computing game."""

__version__ = "1.0.0"


def main():
    """Launch the game."""
    import arcade

    from quanta_quest.constants import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
    from quanta_quest.views import MainMenu

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MainMenu()
    window.show_view(menu_view)
    arcade.run()
