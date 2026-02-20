"""Sprite classes for Quanta Quest."""

import arcade

from quanta_quest.assets import asset_path
from quanta_quest.constants import (
    BALL_SCALING,
    CHARACTER_SCALING,
    GATE_SCALING,
    LEFT_FACING,
    RIGHT_FACING,
)


def load_texture_vpair(filename):
    """Load a texture pair, with the second being a vertical mirror image."""
    tex = arcade.load_texture(filename)
    return [tex, tex.flip_vertically()]


def load_texture_pair(filename):
    """Load a texture pair, with the second being a horizontal mirror image."""
    tex = arcade.load_texture(filename)
    return [tex, tex.flip_horizontally()]


class QuantumGate(arcade.Sprite):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.scale = GATE_SCALING
        self.texture = arcade.load_texture(asset_path(f"score_{name}.png"))


class QuantumBall(arcade.Sprite):

    def __init__(self, idle_state):
        super().__init__()

        self.scale = BALL_SCALING
        self.master = None
        self.message_index = None
        self.textures = []
        self.textures += load_texture_vpair(asset_path("ball_white.png"))
        self.textures += load_texture_vpair(asset_path("ball_black.png"))
        self.textures += load_texture_vpair(asset_path("ball_up_up.png"))
        self.textures += load_texture_vpair(asset_path("ball_up_down.png"))

        self.state = idle_state
        self.texture = self.textures[self.state]

    def update_animation(self, delta_time: float = 1 / 60):
        self.texture = self.textures[self.state]


class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self):
        super().__init__()

        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING
        self.jumping = False

        main_path = ":resources:images/animated_characters/female_person/femalePerson"

        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        self.texture = self.idle_texture_pair[0]

    def update_animation(self, delta_time: float = 1 / 60):
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction
        ]
