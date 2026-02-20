"""Game views for Quanta Quest."""

import random

import arcade
import arcade.gui
from arcade.camera import Camera2D

from quanta_quest.assets import asset_path
from quanta_quest.constants import (
    BALL_SCALING,
    BGCOLOR,
    GATE_INTERVAL,
    GATE_NUMBER,
    GRAVITY,
    GRID_PIXEL_SIZE,
    MAP_WIDTH,
    PAIR_DISTANCE,
    PLAYER_JUMP_SPEED,
    PLAYER_MOVEMENT_SPEED,
    PLAYER_START_X,
    PLAYER_START_Y,
    SCORE_X,
    SCORE_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_INTERVAL,
    STATE_NUMBER,
    TEXT_WIDTH,
    TILE_SCALING,
    new_zone_x,
)
from quanta_quest.gate_manipulator import gate_on_state, measure_state
from quanta_quest.sprites import PlayerCharacter, QuantumBall, QuantumGate

# --- Instruction messages shown when the player reaches each ball ---
INSTRUCTION_MESSAGES = {
    # Original zones
    0: "The balls can be black or white or some combination of them. The balls can be upright or upside down. The balls can be modified by applying gates on them.",
    1: "Press Alt + X to apply the X gate on this state. You will find that it flips the colour.",
    2: "Press Alt + Z to apply the Z gate. You will find that it rotates the black ball but keeps the white ball unchanged.",
    3: "Press Alt + H to apply the Hadamard gate. You will find that it creates a mixture of both colours.",
    4: "Information can also be stored in pair of balls. The upper one acts as the master ball. Press Alt + C to apply the CNOT gate on the lower ball. It changes the colour of the lower ball if the master ball is black, otherwise leaves the lower ball unchanged.",
    5: "The next step is to create an \"entangled\" pair of balls. This is done by first applying an H gate on the master ball, and then applying a CNOT gate on the lower ball. Try it!",
    6: "The final step is to teleport a black ball to the top of the screen. For this, we have provided you an entangled pair (the two upper balls). First, flip the colour of the lowest ball by applying the appropriate gate.",
    7: "Care to complete a challenge before finishing the game? Apply a single gate on any one of the balls to make them identical.",
    # New concept zones
    8: (
        "QUANTUM MEASUREMENT: When you observe a quantum state, it collapses! "
        "A ball in superposition will randomly become white or black. "
        "Apply the Measurement gate (ALT+M) to these balls and watch the superposition collapse."
    ),
    9: (
        "QUANTUM INTERFERENCE: Quantum operations can cancel each other out, "
        "just like waves can cancel. Apply the Hadamard gate TWICE to this white ball. "
        "Watch it enter superposition, then return to white — because H applied twice equals doing nothing! (H² = I)"
    ),
    10: (
        "THE NO-CLONING THEOREM: A fundamental law of quantum physics says you cannot "
        "perfectly copy an unknown quantum state. The top ball is in superposition. "
        "Try any combination of gates on the bottom ball — you will find it impossible "
        "to make an exact copy of the top ball's state."
    ),
    11: (
        "BELL STATES: There are four maximally entangled two-qubit states called Bell states. "
        "Apply H to the top (master) ball, then CNOT (ALT+C) to the bottom ball to create "
        "the Φ+ (Phi-plus) Bell state! Then do the same for the second pair."
    ),
    12: (
        "QUANTUM RANDOMNESS: Unlike classical coin flips, quantum randomness is "
        "fundamentally unpredictable — guaranteed by the laws of physics! "
        "Apply H then M to each ball to generate truly random bits. "
        "Each measurement is completely independent and perfectly random."
    ),
    13: (
        "DEUTSCH'S ALGORITHM: The simplest quantum algorithm! A mystery oracle function "
        "has already been applied to these balls. Apply H to the top ball, then Measure it (ALT+M). "
        "If it collapses to WHITE → the oracle is CONSTANT. "
        "If it collapses to BLACK → the oracle is BALANCED."
    ),
    14: (
        "QUANTUM ERROR DETECTION: Noise can corrupt quantum information by flipping states. "
        "One of these three white balls has been secretly flipped to black by noise! "
        "Apply the X gate (ALT+X) to the corrupted ball to fix the error. "
        "In real quantum computers, errors are detected using ancilla qubits and CNOT gates."
    ),
}

# --- Messages shown when the player collects a gate ---
GATE_COLLECT_MESSAGES = {
    "X": "You have collected two X gates. You will learn how to use it very soon. You will need these gates later, so keep them handy.",
    "Z": "You have collected two Z gates. You will learn how to use it very soon.",
    "H": "You have collected two Hadamard gates. You will learn how to use it very soon.",
    "C": "You have collected two CNOT gates, which, unlike the other gates, only act on pairs of balls. You will learn how to use it very soon.",
    "M": "You have collected two Measurement gates! Use ALT+M on a ball in superposition to collapse it to a definite white or black state.",
}


class Messagebox(arcade.gui.UIMessageBox):
    def __init__(self, message, game):
        text_height = max(len(message) // TEXT_WIDTH + 150, 180)
        super().__init__(width=TEXT_WIDTH,
                         height=text_height,
                         message_text=message,
                         buttons=["Okay"])
        self.game = game
        self.game.can_move = False
        self.game.is_message = self

    def on_action(self, event):
        self.game.can_move = True
        self.game.is_message = None


class GameView(arcade.View):
    """Main application class."""

    def __init__(self):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.is_message = None
        self.scene = None
        self.player_sprite = None
        self.can_shoot = True
        self.shoot_timer = 0
        self.physics_engine = None
        self.camera = None
        self.gui_camera = None

        self.show_instruction = [True] * 20

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
        self.collected_gates = {"X": 0, "Z": 0, "H": 0, "C": 0, "M": 0}
        self.score_images = {
            "X": arcade.load_texture(asset_path("score_X.png")),
            "Z": arcade.load_texture(asset_path("score_Z.png")),
            "H": arcade.load_texture(asset_path("score_H.png")),
            "C": arcade.load_texture(asset_path("score_C.png")),
            "M": arcade.load_texture(asset_path("score_M.png")),
        }

        self.scene = arcade.Scene()
        self.camera = Camera2D()
        self.background = arcade.load_texture(asset_path("main.png"))
        self.gui_camera = Camera2D()

        # Player setup
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Player", self.player_sprite)

        # Ground tiles
        for x in range(0, int((MAP_WIDTH + 1) * GRID_PIXEL_SIZE), GRID_PIXEL_SIZE):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.scene.add_sprite("Walls", wall)

        # --- ORIGINAL ZONES (unchanged) ---
        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = (0.3 + STATE_NUMBER + 1) * STATE_INTERVAL * GRID_PIXEL_SIZE
        wall.center_y = PLAYER_START_Y + 20 + PAIR_DISTANCE // 2
        self.scene.add_sprite("Walls", wall)

        # Single tutorial balls (indices 0-3)
        for x in range(STATE_NUMBER):
            state = QuantumBall(2 * (1 - x % 2))
            state.center_x = (0.5 + x) * STATE_INTERVAL * GRID_PIXEL_SIZE
            state.center_y = PLAYER_START_Y + 30
            self.scene.add_sprite("States", state)
            state.message_index = x
        self.init_ball = self.scene["States"][0]

        # Paired balls for CNOT + entanglement (indices 4-7)
        for x in range(2):
            state1 = QuantumBall(2 * (1 - x))
            state2 = QuantumBall(x * 2)
            state1.scale = 1.2 * BALL_SCALING
            state2.master = state1
            state2.message_index = STATE_NUMBER + x
            state1.center_x = (0.5 + STATE_NUMBER + x) * STATE_INTERVAL * GRID_PIXEL_SIZE
            state2.center_x = (0.5 + STATE_NUMBER + x) * STATE_INTERVAL * GRID_PIXEL_SIZE
            state1.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE
            state2.center_y = PLAYER_START_Y + 30
            self.scene.add_sprite("States", state1)
            self.scene.add_sprite("States", state2)

        # Teleportation zone (indices 8-10)
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

        # End challenge pair (indices 11-12)
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

        # Original gates (X, Z, H, C)
        for x in range(1, GATE_NUMBER + 1):
            gate = QuantumGate(["X", "Z", "H", "C"][x - 1])
            gate.center_x = x * STATE_INTERVAL * GRID_PIXEL_SIZE
            gate.center_y = PLAYER_START_Y + 32
            self.scene.add_sprite("Gates", gate)

        # --- NEW CONCEPT ZONES ---
        self._setup_new_zones()

        self.scene.add_sprite_list("Items")

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.scene["Walls"]
        )
        self.show_instruction_challenges = [True] * 15
        self.end_of_map = MAP_WIDTH * GRID_PIXEL_SIZE
        self.time = 0

        self.end_of_map_sprite = arcade.Sprite(
            ":resources:images/tiles/signExit.png", TILE_SCALING
        )
        self.end_of_map_sprite.center_x = self.end_of_map
        self.end_of_map_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Items", self.end_of_map_sprite)

    # -----------------------------------------------------------------
    # New zone setup
    # -----------------------------------------------------------------
    def _setup_new_zones(self):
        """Set up the 7 new quantum concept zones."""

        # --- Zone 0: Quantum Measurement ---
        self._place_gate("M", new_zone_x(0) - 2 * GRID_PIXEL_SIZE)

        b1 = self._place_ball(4, new_zone_x(0), message_index=8)
        b2 = self._place_ball(5, new_zone_x(0) + GRID_PIXEL_SIZE)
        self.measurement_balls = [b1, b2]

        # --- Zone 1: Quantum Interference (H² = I) ---
        self._place_gate("H", new_zone_x(1) - 2 * GRID_PIXEL_SIZE)

        b = self._place_ball(0, new_zone_x(1), message_index=9)
        self.interference_ball = b
        self.interference_was_superposition = False

        # --- Zone 2: No-Cloning Theorem ---
        source = self._place_ball(4, new_zone_x(2), y=PLAYER_START_Y + 30 + PAIR_DISTANCE)
        source.scale = 1.2 * BALL_SCALING
        target = self._place_ball(0, new_zone_x(2), message_index=10)
        self.noclone_balls = (source, target)
        self.noclone_message_shown = False

        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = new_zone_x(2) - 120
        wall.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE - 120
        self.scene.add_sprite("Walls", wall)

        # --- Zone 3: Bell States ---
        self._place_gate("H", new_zone_x(3) - 3 * GRID_PIXEL_SIZE)
        self._place_gate("C", new_zone_x(3) - 2 * GRID_PIXEL_SIZE)

        # Pair 1: both start |0⟩ → create Φ+
        upper1 = self._place_ball(0, new_zone_x(3), y=PLAYER_START_Y + 30 + PAIR_DISTANCE)
        upper1.scale = 1.2 * BALL_SCALING
        lower1 = self._place_ball(0, new_zone_x(3), message_index=11)
        lower1.master = upper1

        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = new_zone_x(3) - 120
        wall.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE - 120
        self.scene.add_sprite("Walls", wall)

        # Pair 2: start |1⟩|0⟩ → create Ψ+
        upper2 = self._place_ball(2, new_zone_x(3) + 3 * GRID_PIXEL_SIZE,
                                  y=PLAYER_START_Y + 30 + PAIR_DISTANCE)
        upper2.scale = 1.2 * BALL_SCALING
        lower2 = self._place_ball(0, new_zone_x(3) + 3 * GRID_PIXEL_SIZE)
        lower2.master = upper2

        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = new_zone_x(3) + 3 * GRID_PIXEL_SIZE - 120
        wall.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE - 120
        self.scene.add_sprite("Walls", wall)

        self.bell_pairs = [(upper1, lower1), (upper2, lower2)]
        self.bell_done = [False, False]

        # --- Zone 4: Quantum Randomness ---
        self._place_gate("M", new_zone_x(4) - 3 * GRID_PIXEL_SIZE)
        self._place_gate("H", new_zone_x(4) - 2 * GRID_PIXEL_SIZE)

        self.random_balls = []
        for i in range(4):
            b = self._place_ball(0, new_zone_x(4) + i * GRID_PIXEL_SIZE,
                                 message_index=12 if i == 0 else None)
            self.random_balls.append(b)
        self.random_measured_count = 0

        # --- Zone 5: Deutsch's Algorithm ---
        self._place_gate("H", new_zone_x(5) - 3 * GRID_PIXEL_SIZE)
        self._place_gate("M", new_zone_x(5) - 2 * GRID_PIXEL_SIZE)

        # Oracle type: constant → input stays |+⟩, balanced → input becomes |−⟩
        self.deutsch_oracle = random.choice(["constant", "balanced"])
        if self.deutsch_oracle == "constant":
            input_state = 4  # |+⟩ — after H will become |0⟩ (white)
        else:
            input_state = 5  # |−⟩ — after H will become |1⟩ (black)

        input_ball = self._place_ball(input_state, new_zone_x(5),
                                      y=PLAYER_START_Y + 30 + PAIR_DISTANCE,
                                      message_index=13)
        output_ball = self._place_ball(5, new_zone_x(5))

        wall = arcade.Sprite(":resources:images/tiles/dirtHalf_mid.png", TILE_SCALING)
        wall.center_x = new_zone_x(5) - 120
        wall.center_y = PLAYER_START_Y + 30 + PAIR_DISTANCE - 120
        self.scene.add_sprite("Walls", wall)

        self.deutsch_balls = (input_ball, output_ball)
        self.deutsch_answered = False

        # --- Zone 6: Quantum Error Detection ---
        self._place_gate("X", new_zone_x(6) - 2 * GRID_PIXEL_SIZE)

        self.error_balls = []
        self.error_index = random.randint(0, 2)
        for i in range(3):
            init_state = 2 if i == self.error_index else 0
            b = self._place_ball(init_state, new_zone_x(6) + i * GRID_PIXEL_SIZE,
                                 message_index=14 if i == 0 else None)
            self.error_balls.append(b)
        self.error_fixed = False

    def _place_ball(self, state, x, y=None, message_index=None):
        """Helper to place a QuantumBall in the scene."""
        ball = QuantumBall(state)
        ball.center_x = x
        ball.center_y = y if y is not None else PLAYER_START_Y + 30
        ball.message_index = message_index
        self.scene.add_sprite("States", ball)
        return ball

    def _place_gate(self, name, x):
        """Helper to place a gate collectible in the scene."""
        gate = QuantumGate(name)
        gate.center_x = x
        gate.center_y = PLAYER_START_Y + 32
        self.scene.add_sprite("Gates", gate)

    # -----------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------
    def on_draw(self):
        """Render the screen."""
        self.clear()

        arcade.draw_texture_rect(
            self.background,
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
        )

        self.camera.use()
        self.scene.draw()

        self.gui_camera.use()

        for j, (g, v) in enumerate(self.collected_gates.items()):
            image = self.score_images[g]
            for i in range(v):
                cx = (1.5 * j + 1) * SCORE_X
                cy = SCORE_Y - 100 * i
                hw = image.width // 4
                hh = image.height // 4
                arcade.draw_texture_rect(
                    image,
                    arcade.LRBT(cx - hw, cx + hw, cy - hh, cy + hh),
                )

        self.manager.draw()

    # -----------------------------------------------------------------
    # Input handling
    # -----------------------------------------------------------------
    def process_keychange(self):
        if self.up_pressed and not self.down_pressed:
            if (
                self.physics_engine.can_jump(y_distance=10)
                and not self.jump_needs_reset
            ):
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)

        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
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
        elif key == arcade.key.ENTER and self.is_message is not None:
            self.manager.remove(self.is_message)
            self.can_move = True
            self.is_message = None

        self.process_keychange()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
            self.jump_needs_reset = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        for hit_state in arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["States"]
        ):
            # --- Standard gate applications (X, Z, H, C) ---
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
                and hit_state.master is not None and self.collected_gates['C'] > 0
                ):
                hit_state.state = gate_on_state(hit_state.state, 'C', hit_state.master.state)
                self.collected_gates['C'] -= 1
                arcade.play_sound(self.shoot_sound)

            # --- Measurement gate (M) ---
            if key == arcade.key.M and (modifiers & arcade.key.MOD_ALT):
                state_idx = self.scene["States"].index(hit_state)

                # Original teleportation Bell measurement (unchanged)
                if (state_idx == STATE_NUMBER + 4
                    and self.show_instruction_challenges[1] is False
                    ):
                    self.scene["States"][STATE_NUMBER + 4].state = 4
                    self.scene["States"][STATE_NUMBER + 5].state = 4
                    self.scene["States"][STATE_NUMBER + 6].state = 2 * random.randint(0, 1)
                    message_box = arcade.gui.UIMessageBox(
                        width=400,
                        height=250,
                        message_text=(
                            "Note that the upper ball has now become non-entangled. "
                            "Complete the teleportation by figuring out the correct gate "
                            "(X/Z/H) that will convert the upper ball into the black ball "
                            "we wanted to teleport. Answer by clicking one of the buttons."
                        ),
                        buttons=["X gate", "Z gate", "H gate"]
                    )

                    @message_box.event("on_action")
                    def on_action(event):
                        self.on_final_message_close(event.action)

                    self.manager.add(message_box)

                # General measurement (new zones)
                elif self.collected_gates.get('M', 0) > 0:
                    old_state = hit_state.state
                    hit_state.state = measure_state(hit_state.state)
                    self.collected_gates['M'] -= 1
                    arcade.play_sound(self.shoot_sound)

                    if old_state >= 4:
                        result = "WHITE (|0⟩)" if hit_state.state == 0 else "BLACK (|1⟩)"
                        messagebox = Messagebox(
                            f"Measurement collapsed the superposition to {result}! "
                            "Each measurement is random — try again for a different result.",
                            self)
                        self.manager.add(messagebox)

            # --- Original end-of-game challenge check ---
            if ((self.scene["States"].index(hit_state) == STATE_NUMBER + 7
                 or self.scene["States"].index(hit_state) == STATE_NUMBER + 8)
                and key in (arcade.key.X, arcade.key.Z, arcade.key.H, arcade.key.C)
                ):
                if self.scene["States"][STATE_NUMBER + 7].state == self.scene["States"][STATE_NUMBER + 8].state:
                    messagebox = Messagebox("Great! You have finished the original challenges. Keep walking to discover new quantum concepts!", self)
                    self.manager.add(messagebox)
                else:
                    messagebox = Messagebox("Oops! That didn't work. Try again?", self)
                    self.manager.add(messagebox)

        self.process_keychange()

    def on_final_message_close(self, button_text):
        self.scene["States"][STATE_NUMBER + 6].state = gate_on_state(
            self.scene["States"][STATE_NUMBER + 6].state, button_text[0]
        )
        if self.scene["States"][STATE_NUMBER + 6].state in [2, 3]:
            messagebox = Messagebox(
                "Nicely done! You have successfully teleported the ball. "
                "Proceed to discover new quantum concepts!", self)
            self.manager.add(messagebox)
        else:
            messagebox = Messagebox(
                "Sadly, that wasn't the correct answer. You will have to start from the beginning.", self)
            self.manager.add(messagebox)
            self.end_timer = 1

    # -----------------------------------------------------------------
    # Camera
    # -----------------------------------------------------------------
    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0

        self.camera.position = (
            screen_center_x + self.camera.viewport_width / 2,
            screen_center_y + self.camera.viewport_height / 2,
        )

    # -----------------------------------------------------------------
    # Game loop
    # -----------------------------------------------------------------
    def on_update(self, delta_time):
        self.time += 1
        if self.time == 100:
            self.init_ball.state = (self.init_ball.state + 1) % 8
            self.time = 0
        for state in self.scene["States"]:
            state.update_animation()

        if self.can_move:
            self.physics_engine.update()

        if self.player_sprite.center_x > PLAYER_START_X and self.show_instruction[0]:
            messagebox = Messagebox(
                "Our explorer suddenly finds herself in the quantum world. "
                "In this world, information is stored in the colour and orientation of balls.",
                self)
            self.manager.add(messagebox)
            self.left_pressed, self.right_pressed, self.up_pressed = False, False, False
            self.down_pressed, self.jump_needs_reset, self.shoot_pressed = False, False, False
            self.show_instruction[0] = False

        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        self.process_keychange()
        self.scene.update_animation(delta_time, ["Player"])
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

        # --- Original zone checks ---
        if self.scene["States"][STATE_NUMBER + 4].state == 2 and self.show_instruction_challenges[1] is True:
            messagebox = Messagebox(
                "Great. The next step is to perform a \"Bell measurement\" on the pair "
                "of lower balls, by pressing ALT+M on the lowest ball. This will "
                "transfer the entanglement to the lower balls.", self)
            self.manager.add(messagebox)
            self.show_instruction_challenges[1] = False

        if (self.player_sprite.center_x >= (1.5 + STATE_NUMBER) * STATE_INTERVAL * GRID_PIXEL_SIZE
            + self.scene["States"][STATE_NUMBER + 3].width):
            if (self.scene["States"][STATE_NUMBER + 2].state == 4
                and self.scene["States"][STATE_NUMBER + 3].state == 4
                and self.show_instruction_challenges[0]):
                messagebox = Messagebox(
                    "Well done! You can see the entanglement in the fact that the colours "
                    "of the two halves are correlated: white is above white and black is "
                    "above black. Have another hadamard!", self)
                self.collected_gates['H'] += 1
                self.show_instruction_challenges[0] = False
                self.show_instruction_challenges[3] = False
                self.show_instruction_challenges[2] = False
                self.manager.add(messagebox)
            elif (self.scene["States"][STATE_NUMBER + 2].state == 2
                  and self.scene["States"][STATE_NUMBER + 3].state == 0
                  and self.show_instruction_challenges[2]):
                messagebox = Messagebox(
                    "It seems like you skipped it. It would be useful if you learnt "
                    "this before proceeding.", self)
                self.show_instruction_challenges[2] = False
                self.manager.add(messagebox)
            elif self.show_instruction_challenges[3]:
                messagebox = Messagebox(
                    "I don't think you applied the correct operations. Want to try "
                    "again before proceeding?", self)
                self.show_instruction_challenges[3] = False
                self.manager.add(messagebox)

        # --- New zone checks ---
        self._check_new_zones()

        # --- End of map ---
        if self.player_sprite.center_x >= self.end_of_map:
            game_over_view = GameOverView()
            self.window.show_view(game_over_view)

        # --- Instruction messages (triggered by collision) ---
        state_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["States"]
        )
        for state in state_hit_list:
            if state.message_index is not None:
                message = INSTRUCTION_MESSAGES.get(state.message_index)
                if message and self.show_instruction[state.message_index + 1]:
                    messagebox = Messagebox(message, self)
                    self.manager.add(messagebox)
                    self.show_instruction[state.message_index + 1] = False

        # --- Gate collection ---
        gate_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Gates"]
        )
        for gate in gate_hit_list:
            message = GATE_COLLECT_MESSAGES.get(
                gate.name,
                f"You collected two {gate.name} gates!"
            )
            messagebox = Messagebox(message, self)
            self.manager.add(messagebox)
            self.collected_gates[gate.name] += 2
            arcade.play_sound(self.collect_coin_sound)
            gate.remove_from_sprite_lists()

    # -----------------------------------------------------------------
    # New zone challenge checks
    # -----------------------------------------------------------------
    def _check_new_zones(self):
        """Check progress on new concept zones."""
        px = self.player_sprite.center_x

        # Zone 1: Interference — detect H² = I
        if (self.interference_ball.state >= 4
            and not self.interference_was_superposition):
            self.interference_was_superposition = True

        if (self.interference_was_superposition
            and self.interference_ball.state == 0
            and self.show_instruction_challenges[4]):
            messagebox = Messagebox(
                "Excellent! The ball returned to white. H applied twice equals the identity — "
                "the quantum waves interfered destructively and cancelled out. "
                "This is the foundation of many quantum algorithms!", self)
            self.manager.add(messagebox)
            self.show_instruction_challenges[4] = False

        # Zone 2: No-Cloning — after player walks past, explain the theorem
        if (px > new_zone_x(2) + 2 * GRID_PIXEL_SIZE
            and not self.noclone_message_shown
            and not self.show_instruction[10 + 1]):
            source, target = self.noclone_balls
            if target.state != source.state:
                messagebox = Messagebox(
                    "As you discovered, there is no gate combination that can perfectly "
                    "copy an unknown quantum state. This is the No-Cloning Theorem — "
                    "a cornerstone of quantum cryptography and information theory!", self)
                self.manager.add(messagebox)
            self.noclone_message_shown = True

        # Zone 3: Bell States — detect successful entanglement
        for i, (upper, lower) in enumerate(self.bell_pairs):
            if (upper.state >= 4 and lower.state >= 4
                and not self.bell_done[i]):
                label = "Φ+ (Phi-plus)" if i == 0 else "Ψ+ (Psi-plus)"
                messagebox = Messagebox(
                    f"You created the {label} Bell state! The two balls are now "
                    "maximally entangled — measuring one instantly determines the other, "
                    "no matter how far apart they are.", self)
                self.manager.add(messagebox)
                self.bell_done[i] = True

        # Zone 4: Quantum Randomness — count measurements
        measured = sum(1 for b in self.random_balls if b.state in [0, 2])
        if (measured >= 4
            and measured > self.random_measured_count
            and self.show_instruction_challenges[5]):
            bits = "".join("0" if b.state == 0 else "1" for b in self.random_balls)
            messagebox = Messagebox(
                f"You generated the random bit string: {bits}! "
                "Unlike pseudo-random numbers from classical computers, these bits are "
                "guaranteed to be truly random by quantum mechanics. This is the basis "
                "of quantum random number generators used in cryptography.", self)
            self.manager.add(messagebox)
            self.show_instruction_challenges[5] = False
        self.random_measured_count = measured

        # Zone 5: Deutsch's Algorithm — check if player measured the input ball
        input_ball, output_ball = self.deutsch_balls
        if (input_ball.state in [0, 2]
            and not self.deutsch_answered
            and not self.show_instruction[13 + 1]):
            result = "CONSTANT" if input_ball.state == 0 else "BALANCED"
            correct = result == self.deutsch_oracle.upper()
            if correct:
                messagebox = Messagebox(
                    f"The measurement shows {result} — that's correct! "
                    "A classical computer would need to query the oracle TWICE, "
                    "but the quantum algorithm determined the answer in just ONE query. "
                    "This is quantum speedup!", self)
            else:
                messagebox = Messagebox(
                    f"The measurement collapsed to {'white' if input_ball.state == 0 else 'black'}. "
                    f"The oracle was actually {self.deutsch_oracle}. "
                    "Try applying H to the input ball before measuring next time!", self)
            self.manager.add(messagebox)
            self.deutsch_answered = True

        # Zone 6: Error Detection — check if all balls are white
        if (all(b.state == 0 for b in self.error_balls)
            and not self.error_fixed
            and not self.show_instruction[14 + 1]):
            messagebox = Messagebox(
                "Error corrected! You identified and fixed the corrupted qubit. "
                "Real quantum error correction uses sophisticated codes (like the "
                "surface code) with many ancilla qubits to detect and fix errors "
                "without directly measuring the data qubits.", self)
            self.manager.add(messagebox)
            self.error_fixed = True


class PauseMenu(arcade.View):

    def __init__(self, prev_view):
        super().__init__()
        self.prev_view = prev_view

    def on_show_view(self):
        arcade.set_background_color(BGCOLOR)

    def on_draw(self):
        self.clear()
        image = arcade.load_texture(asset_path("opening_cropped.png"))
        arcade.draw_texture_rect(
            image,
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
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
        arcade.set_background_color(BGCOLOR)

    def on_draw(self):
        self.clear()
        image = arcade.load_texture(asset_path("opening_cropped.png"))
        arcade.draw_texture_rect(
            image,
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
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
            "Click or press Enter to start playing.\n"
            "Move and jump using arrow keys or W/A/S/D.\n"
            "While playing, press Escape to exit or restart the game.",
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
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
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
        game_view = GameView()
        self.window.show_view(game_view)
