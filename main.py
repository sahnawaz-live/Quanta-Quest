"""
Platformer Game
"""
import arcade
import arcade.gui
import os
import random
from gate_manipulator import gate_on_state

# Constants
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 1000
SCORE_Y = SCREEN_HEIGHT - 50
SCORE_X = 70
DEFAULT_LINE_HEIGHT = 45
SCREEN_TITLE = "Quanta Quest"

# Constants used to scale our sprites from their original size
CHARACTER_SCALING = 1
TILE_SCALING = 1
COIN_SCALING = 0.5
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING
NUM_CRATES = 6
CRATE_HEIGHT = 160
CRATE_OFFSET = 100

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 22
RIGHT_FACING = 0
LEFT_FACING = 1
PLAYER_START_X = SPRITE_PIXEL_SIZE * TILE_SCALING * 1
PLAYER_START_Y = SPRITE_PIXEL_SIZE * TILE_SCALING * 1

BUTTON_POS_X = SCREEN_WIDTH // 2 - 150
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 100
DISTANCE = 150
BUTTON_POS_Y = SCREEN_HEIGHT // 2

ENEMY_SIZE = 2
ENEMY_SPEED = 2
BULLET_SPEED = 5
BULLET_DAMAGE = 1
ENEMY_HEALTH = 3

SHOOT_INTERVAL = 20
BGCOLOR = arcade.color.JET
FGCOLOR = arcade.color.WHITE
TEXT_WIDTH = 400

GATE_INTERVAL = 5
GATE_NUMBER = 4
STATE_INTERVAL = 5
STATE_NUMBER = 4

MAP_WIDTH = STATE_INTERVAL * STATE_NUMBER + GATE_INTERVAL * (GATE_NUMBER + 0.5)
BALL_SCALING = 0.8
GATE_SCALING = 0.9
PAIR_DISTANCE = 200

def load_texture_vpair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_vertically=True),
    ]


class QuantumGate(arcade.Sprite):
    def __init__(self,name):
        super().__init__()
        self.name = name
        self.scale = GATE_SCALING
        self.texture = arcade.load_texture("score_{}.png".format(name))



class QuantumBall(arcade.Sprite):

    def __init__(self, idle_state):

        # Set up parent class
        super().__init__()

        # Load textures for idle standing
        self.scale = BALL_SCALING
        self.master = None
        self.message_index = None
        self.textures = []
        self.textures += load_texture_vpair("ball_white.png")
        self.textures += load_texture_vpair("ball_black.png")
        self.textures += load_texture_vpair("ball_up_up.png")
        self.textures += load_texture_vpair("ball_up_down.png")

        self.state = idle_state
        self.texture = self.textures[self.state]
        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):
        self.texture = self.textures[self.state]


class Messagebox(arcade.gui.UIMessageBox):
    def __init__(self, message, game):
        text_height = max(len(message) // TEXT_WIDTH + 150, 180)
        super().__init__(width=TEXT_WIDTH, 
                         height=text_height, 
                         message_text=message, 
                         buttons=["Okay"],
                         callback=self.on_message_box_close)
        self.game = game
        self.game.can_move = False
        self.game.is_message = self
    def on_message_box_close(self, button_text):
        self.game.can_move = True
        self.game.is_message = None


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.jumping = False


        # Images from Kenney.nl's Asset Pack 3
        main_path = ":resources:images/animated_characters/female_person/femalePerson"

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)


        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):
        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Jumping animation
        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction
        ]

class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.is_message = None

        # Our Scene Object
        self.scene = None

        # Separate variable that holds the player sprite
        self.player_sprite = None
        self.can_shoot = True
        self.shoot_timer = 0

        # Our physics engine
        self.physics_engine = None

        # A Camera that can be used for scrolling the screen
        self.camera = None


        # A Camera that can be used to draw GUI elements

        self.gui_camera = None

        self.show_instruction = [True] * 10;

        # Keep track of the score


        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False
        self.shoot_pressed = False
        self.can_move = True

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        self.game_over = arcade.load_sound(":resources:sounds/gameover1.wav")
        self.shoot_sound = arcade.load_sound(":resources:sounds/hurt5.wav")
        self.hit_sound = arcade.load_sound(":resources:sounds/hit5.wav")
        self.hurt_sound = arcade.load_sound(":resources:sounds/explosion2.wav")

        self.background = None
        self.collected_gates = {"X":0, "Z":0, "H":0, "C":0}
        self.score_images = {"X": arcade.load_texture("score_X.png"),
                             "Z": arcade.load_texture("score_Z.png"), 
                             "H": arcade.load_texture("score_H.png"),
                             "C": arcade.load_texture("score_C.png")
                             }

        self.scene = arcade.Scene()

        # Set up the Game Camera
        self.camera = arcade.Camera(self.window.width, self.window.height)

        self.background = arcade.load_texture("./main.png")

        # Set up the GUI Camera

        self.gui_camera = arcade.Camera(self.window.width, self.window.height)

        # Initialize Scene

        # Set up the player, specifically placing it at these coordinates.
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Player", self.player_sprite)

        for x in range(0, int((MAP_WIDTH + 1) * GRID_PIXEL_SIZE), GRID_PIXEL_SIZE):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.scene.add_sprite("Walls", wall)
        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = (0.3 + STATE_NUMBER + 1) * STATE_INTERVAL * GRID_PIXEL_SIZE
        wall.center_y = PLAYER_START_Y + 20 + PAIR_DISTANCE // 2
        self.scene.add_sprite("Walls", wall)

        for x in range(STATE_NUMBER):
            state = QuantumBall(2 * (1 - x % 2))
            state.center_x = (0.5 + x) * STATE_INTERVAL * GRID_PIXEL_SIZE
            state.center_y = PLAYER_START_Y + 30
            self.scene.add_sprite("States", state)
            state.message_index = x
        self.init_ball = self.scene["States"][0]

        for x in range(2):
            state1 = QuantumBall(2*(1-x))
            state2 = QuantumBall(x*2)
            state1.scale = 1.2 * BALL_SCALING
            state2.master = state1
            state2.message_index = STATE_NUMBER + x
            state1.center_x = (0.5 + STATE_NUMBER + x) * STATE_INTERVAL * GRID_PIXEL_SIZE
            state2.center_x = (0.5 + STATE_NUMBER + x) * STATE_INTERVAL * GRID_PIXEL_SIZE
            state1.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE
            state2.center_y = PLAYER_START_Y + 30
            self.scene.add_sprite("States", state1)
            self.scene.add_sprite("States", state2)

        state_C = QuantumBall(0)
        state_A = QuantumBall(4)
        state_B = QuantumBall(4)

        state_C.message_index = STATE_NUMBER + 2

        state_C.center_x = (0.5 + STATE_NUMBER + 2) * STATE_INTERVAL * GRID_PIXEL_SIZE
        state_A.center_x = (0.5 + STATE_NUMBER + 2) * STATE_INTERVAL * GRID_PIXEL_SIZE
        state_B.center_x = (0.5 + STATE_NUMBER + 2) * STATE_INTERVAL * GRID_PIXEL_SIZE

        state_C.center_y = PLAYER_START_Y + 30
        state_A.center_y = PLAYER_START_Y + 250
        state_B.center_y = 0.8 * SCREEN_HEIGHT

        self.scene.add_sprite("States", state_C)
        self.scene.add_sprite("States", state_A)
        self.scene.add_sprite("States", state_B)

        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = state_A.center_x - 120
        wall.center_y = state_A.center_y - 120
        self.scene.add_sprite("Walls", wall)
        self.end_timer = 0


        state1 = QuantumBall(0)
        state2 = QuantumBall(4)
        state2.message_index = STATE_NUMBER + 3
        state1.message_index = STATE_NUMBER + 3
        state1.center_x = (0.5 + STATE_NUMBER + 3) * STATE_INTERVAL * GRID_PIXEL_SIZE
        state2.center_x = (0.5 + STATE_NUMBER + 3) * STATE_INTERVAL * GRID_PIXEL_SIZE
        state1.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE
        state2.center_y = PLAYER_START_Y + 30
        self.scene.add_sprite("States", state1)
        self.scene.add_sprite("States", state2)
        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = state1.center_x - 120
        wall.center_y = state1.center_y - 120
        self.scene.add_sprite("Walls", wall)


        for x in range(1, GATE_NUMBER+1):
            gate = QuantumGate(["X","Z","H","C"][x-1])
            gate.center_x = x * STATE_INTERVAL * GRID_PIXEL_SIZE
            gate.center_y = PLAYER_START_Y + 32
            self.scene.add_sprite("Gates", gate)

        self.scene.add_sprite_list("Items")

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.scene["Walls"]
        )
        self.show_instruction_challenges = [True]*4
        self.end_of_map = MAP_WIDTH * GRID_PIXEL_SIZE
        self.time = 0

        self.end_of_map_sprite = arcade.Sprite(
                ":resources:images/tiles/signExit.png", TILE_SCALING
            )
        self.end_of_map_sprite.center_x = self.end_of_map
        self.end_of_map_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Items", self.end_of_map_sprite)


    def on_draw(self):
        """Render the screen."""

        self.clear()

        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        self.camera.use()

        # Draw our Scene
        self.scene.draw()

        # Activate the GUI camera before drawing GUI elements

        self.gui_camera.use()

        # Draw our score on the screen, scrolling it with the viewport

        for j,(g,v) in enumerate(self.collected_gates.items()):
            image = self.score_images[g]
            for i in range(v):
                arcade.draw_texture_rectangle((1.5 * j + 1) * SCORE_X,
                                              SCORE_Y - 100 * i,
                                              image.width // 2,
                                              image.height // 2,
                                              image)

        self.manager.draw()


    def process_keychange(self):
        """
        Called when we change a key up/down or we move on/off a ladder.
        """
        # Process up/down
        if self.up_pressed and not self.down_pressed:
            if (
                self.physics_engine.can_jump(y_distance=10)
                and not self.jump_needs_reset
            ):
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)


        # Process left/right
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.ESCAPE:
            pause_view = PauseMenu(self)
            self.window.show_view(pause_view)
        elif key == arcade.key.ENTER and self.is_message != None:
            self.manager.remove(self.is_message)
            self.can_move = True
            self.is_message = None

        self.process_keychange()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
            self.jump_needs_reset = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        for hit_state in arcade.check_for_collision_with_list(self.player_sprite, self.scene["States"]):
            if key == arcade.key.X and (modifiers & arcade.key.MOD_ALT) and self.collected_gates['X'] > 0:
                hit_state.state = gate_on_state(hit_state.state, 'X')
                self.collected_gates['X'] -= 1
                arcade.play_sound(self.shoot_sound)
            if key == arcade.key.Z and (modifiers & arcade.key.MOD_ALT) and self.collected_gates['Z'] > 0:
                hit_state.state = gate_on_state(hit_state.state, 'Z')
                self.collected_gates['Z'] -= 1
                arcade.play_sound(self.shoot_sound)
            if key == arcade.key.H and (modifiers & arcade.key.MOD_ALT) and self.collected_gates['H'] > 0:
                hit_state.state = gate_on_state(hit_state.state, 'H')
                self.collected_gates['H'] -= 1
                arcade.play_sound(self.shoot_sound)
            if (key == arcade.key.C and (modifiers & arcade.key.MOD_ALT)
                and hit_state.master != None and self.collected_gates['C'] > 0
                ):
                hit_state.state = gate_on_state(hit_state.state, 'C', hit_state.master.state)
                self.collected_gates['C'] -= 1
                arcade.play_sound(self.shoot_sound)
            if (self.scene["States"].index(hit_state) == STATE_NUMBER + 4 
                and self.show_instruction_challenges[1] == False 
                and key == arcade.key.M and (modifiers & arcade.key.MOD_ALT)
                ):
                    self.scene["States"][STATE_NUMBER + 4].state = 4
                    self.scene["States"][STATE_NUMBER + 5].state = 4
                    self.scene["States"][STATE_NUMBER + 6].state = 2 * random.randint(0, 1)
                    message_box = arcade.gui.UIMessageBox(
                        width=400,
                        height=250,
                        message_text=(
                            "Note that the upper ball has now become non-entangled. Complete the teleportation by figuring out the correct gate (X/Z/H) that will convert the upper ball into the black ball we wanted to teleport. Answer by clicking one of the buttons."
                        ),
                        callback=self.on_final_message_close,
                        buttons=["X gate", "Z gate", "H gate"]
                    )
                    self.manager.add(message_box)
            if ((self.scene["States"].index(hit_state) == STATE_NUMBER + 7 
                 or self.scene["States"].index(hit_state) == STATE_NUMBER + 8)
                and key in (arcade.key.X, arcade.key.Z, arcade.key.H, arcade.key.C)
                ):
                if self.scene["States"][STATE_NUMBER + 7].state == self.scene["States"][STATE_NUMBER + 8].state:
                    messagebox = Messagebox("Great! You have finished the game.", self)
                    self.manager.add(messagebox)
                else:
                    messagebox = Messagebox("Oops! That did't work. Try again?", self)
                    self.manager.add(messagebox)



        self.process_keychange()

    def on_final_message_close(self, button_text):
        self.scene["States"][STATE_NUMBER + 6].state = gate_on_state(self.scene["States"][STATE_NUMBER + 6].state, button_text[0])
        if self.scene["States"][STATE_NUMBER + 6].state in [2, 3]:
            messagebox = Messagebox("Nicely done! You have successfully teleported the ball. Proceed to complete the game.", self)
            self.manager.add(messagebox)
        else:
            messagebox = Messagebox("Sadly, that wasn't the correct answer. You will have to start from the beginning.", self)
            self.manager.add(messagebox)
            self.end_timer = 1

        


    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)


    def on_update(self, delta_time):

        self.time += 1
        if self.time == 100:
            self.init_ball.state = (self.init_ball.state + 1) % 8
            self.time = 0
        for state in self.scene["States"]:
            state.update_animation()

        # Move the player with the physics engine
        if self.can_move: self.physics_engine.update()

        if self.player_sprite.center_x > PLAYER_START_X and self.show_instruction[0]:
            messagebox = Messagebox("Our explorer suddenly finds herself in the quantum world. In this world, information is stored in the colour and orientation of balls.", self)
            self.manager.add(messagebox)

            self.left_pressed, self.right_pressed, self.up_pressed, self.down_pressed, self.jump_needs_reset, self.shoot_pressed = [False] * 6
            self.show_instruction[0] = False


        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        self.process_keychange()

        self.scene.update_animation(
            delta_time, ["Player"]
        )

        self.center_camera_to_player()

        if self.end_timer > 0:
            self.end_timer += 1
            if self.end_timer == 200:
                game_over_view = GameOverView()
                self.window.show_view(game_over_view)

        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

            arcade.play_sound(self.game_over)

        if self.scene["States"][STATE_NUMBER + 4].state == 2 and self.show_instruction_challenges[1] == True:
            messagebox = Messagebox("Great. The next step is to perform a \"Bell measurement\" on the pair of lower balls, by pressing ALT+M on the lowest ball. This will transfer the entanglement to the lower balls.", self)
            self.manager.add(messagebox)
            self.show_instruction_challenges[1] = False

        if (self.player_sprite.center_x >= (1.5 + STATE_NUMBER) * STATE_INTERVAL * GRID_PIXEL_SIZE
            + self.scene["States"][STATE_NUMBER + 3].width):
            if self.scene["States"][STATE_NUMBER + 2].state == 4 and self.scene["States"][STATE_NUMBER + 3].state == 4 and self.show_instruction_challenges[0]:
                messagebox = Messagebox("Well done! You can see the entanglement in the fact that the colours of the two halves are correlated: white is above white and black is above black. Have another hadamard!", self)
                self.collected_gates['H'] += 1
                self.show_instruction_challenges[0] = False
                self.show_instruction_challenges[3] = False
                self.show_instruction_challenges[2] = False
                self.manager.add(messagebox)
            elif self.scene["States"][STATE_NUMBER + 2].state == 2 and self.scene["States"][STATE_NUMBER + 3].state == 0 and self.show_instruction_challenges[2]:
                messagebox = Messagebox("It seems like you skipped it. It would be useful if you learnt this before proceeding.", self)
                self.show_instruction_challenges[2] = False
                self.manager.add(messagebox)
            elif self.show_instruction_challenges[3]:
                messagebox = Messagebox("I don't think you applied the correct operations. Want to try again before proceeding?", self)
                self.show_instruction_challenges[3] = False
                self.manager.add(messagebox)

        if self.player_sprite.center_x >= self.end_of_map:
            game_over_view = GameOverView()
            self.window.show_view(game_over_view)

        state_hit_list = arcade.check_for_collision_with_list(
                    self.player_sprite, self.scene["States"]
                )
        for state in state_hit_list:
            if state.message_index != None:
                message = ["The balls can be black or white or some combination of them. The balls can be upright or upside down. The balls can be modified by applying gates on them.",
                           "Press Alt + X to apply the X gate on this state. You will find that it flips the colour.",
                           "Press Alt + Z to apply the Z gate. You will find that it rotates the black ball but keeps the white ball unchanged.",
                           "Press Alt + H to apply the Hadamard gate. You will find that it creates a mixture of both colours.",
                           "Information can also be stored in pair of balls. The upper one acts as the master ball. Press Alt + C to apply the CNOT gate on the lower ball. It changes the colour of the lower ball if the master ball is black, otherwise leaves the lower ball unchanged.",
                           "The next step is to create an \"entangled\" pair of balls. This is done by first applying an H gate on the master ball, and then applying a CNOT gate on the lower ball. Try it!",
                           "The final step is to teleport a black ball to the top of the screen. For this, we have provided you an entangled pair (the two upper balls). First, flip the colour of the lowest ball by applying the appropriate gate.",
                           "Care to complete a challenge before finishing the game? Apply a single gate on any one of the balls to make them identical.",
                           ][state.message_index]

                if self.show_instruction[state.message_index + 1]:
                    messagebox = Messagebox(message, self)
                    self.manager.add(messagebox)
                    self.show_instruction[state.message_index + 1] = False


        gate_hit_list = arcade.check_for_collision_with_list(
                    self.player_sprite, self.scene["Gates"]
                )

        for gate in gate_hit_list:
            message = ["You have collected two X gates. You will learn how to use it very soon. You will need these gates later, so keep them handy.",
                       "You have collected two Z gates. You will learn how to use it very soon.",
                       "You have collected two Hadamard gates. You will learn how to use it very soon.",
                       "You have collected two CNOT gates, which, unlike the other gates, only act on pairs of balls. You will learn how to use it very soon.",
                       ][GATE_NUMBER - len(self.scene["Gates"])]

            messagebox = Messagebox(message, self)
            self.manager.add(messagebox)
            self.collected_gates[gate.name] += 2
            arcade.play_sound(self.collect_coin_sound)
            gate.remove_from_sprite_lists()


class PauseMenu(arcade.View):

    def __init__(self,prev_view):
        super().__init__()
        self.prev_view = prev_view

    def on_show_view(self):
        """Called when switching to this view."""
        arcade.set_background_color(BGCOLOR)

    def on_draw(self):
        """Draw the menu"""
        self.clear()
        image = arcade.load_texture("opening_cropped.png")
        arcade.draw_texture_rectangle(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            SCREEN_WIDTH, SCREEN_HEIGHT,
            image
        )
        arcade.draw_text(
            "Press enter or click to resume the game.\n\nPress Escape to restart the game.\n\nPress Q to quit.",
            200,
            SCREEN_HEIGHT // 1.5,
            arcade.color.BLACK,
            font_size=35,
            anchor_x="left",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=1000,
            align='left',
        )


    def on_mouse_press(self, x, y, button, modifiers):
        self.window.show_view(self.prev_view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.window.show_view(self.prev_view)
        elif key == arcade.key.ESCAPE:
            game_over_view = GameOverView()
            self.window.show_view(game_over_view)
        elif key == arcade.key.Q:
            arcade.exit()


class MainMenu(arcade.View):
    """Class that manages the 'menu' view."""

    def on_show_view(self):
        """Called when switching to this view."""
        arcade.set_background_color(BGCOLOR)

    def on_draw(self):
        """Draw the menu"""
        self.clear()
        image = arcade.load_texture("opening_cropped.png")
        arcade.draw_texture_rectangle(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            SCREEN_WIDTH, SCREEN_HEIGHT,
            image
        )
        arcade.draw_text(
            "QUANTA QUEST",
            200,
            SCREEN_HEIGHT - 200,
            arcade.color.BLACK,
            font_size=70,
            anchor_x="left",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=900,
            align='left',
        )
        arcade.draw_text(
            "THE JOURNEY OF A QUANTUM EXPLORER",
            200,
            SCREEN_HEIGHT - 350,
            arcade.color.BLACK,
            font_size=40,
            anchor_x="left",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=1200,
            align='left',
        )
        arcade.draw_text(
            "Click or press Enter to start playing.\nMove and jump using arrow keys or W/A/S/D.\nWhile playing, press Escape to exit or restart the game.",
            200,
            SCREEN_HEIGHT // 2,
            arcade.color.BLACK,
            font_size=35,
            anchor_x="left",
            anchor_y="top",
            bold=False,
            multiline=True,
            width=1000,
            align='left',
        )


    def on_mouse_press(self, x, y, button, modifiers):

        game_view = GameView()
        self.window.show_view(game_view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            game_view = GameView()
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            arcade.exit()


class GameOverView(arcade.View):
    """Class to manage the game overview"""

    def on_show_view(self):
        """Called when switching to this view"""
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        """Draw the game overview"""
        self.clear()
        arcade.draw_text(
            "Game Over - Click to restart",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            30,
            anchor_x="center",
        )

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """Use a mouse press to advance to the 'game' view."""
        game_view = GameView()
        self.window.show_view(game_view)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MainMenu()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
