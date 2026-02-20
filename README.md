# Quanta Quest

Quanta Quest is the journey of a quantum explorer to unlock the treasure by learning quantum physics and quantum computing.

## Introduction and Setting

In a world interwoven with quantum mysteries, you are a quantum explorer armed with knowledge and curiosity. Your mission is to navigate through quantum challenges to unlock the ultimate treasure, by solving quantum operations and decrypting a hidden message embedded in the quantum realm.

## Motivation

Quantum computing is a rapidly evolving field with the potential to revolutionize how we solve complex problems. However, the learning curve can be steep, often requiring a strong background in physics and mathematics. This game aims to break down these barriers by providing a fun, interactive way to grasp the fundamentals of quantum mechanics.

### Why Play This Game?

- **For Adventure**: As a quantum explorer, you are on a thrilling quest to find a hidden treasure.
- **For Learning**: Master the basics of quantum gates, superposition, and entanglement through hands-on exercises.
- **For Discovery**: Unveil the fascinating concept of quantum teleportation, a cornerstone of future quantum communication technologies.
- **For Application**: Gain practical skills that could be applied in real-world quantum computing problems.

## Learning Objectives

**Original Zones:**
- Gain hands-on experience with basic quantum gate operations like X, Z, H, CX (Controlled Not).
- Learn the concept of quantum superposition and quantum entanglement.
- Discover the intriguing concept of quantum teleportation in a playful environment.

**New Concept Zones:**
- **Quantum Measurement** — Observe superposition collapse into definite states.
- **Quantum Interference** — See how applying Hadamard twice cancels out (H² = I).
- **No-Cloning Theorem** — Discover why quantum states cannot be perfectly copied.
- **Bell States** — Create all four maximally entangled two-qubit states.
- **Quantum Randomness** — Generate truly random bits using superposition and measurement.
- **Deutsch's Algorithm** — Experience the simplest quantum algorithm and quantum speedup.
- **Quantum Error Detection** — Find and fix corrupted qubits to protect quantum information.

## Video link of the game

[Quanta Quest](https://www.sahnawaz.live)

## How to Play

1. The player starts as a quantum explorer searching for a key to unlock a treasure chest.
2. Learn and apply various quantum gates to proceed through different levels.
3. Assemble a teleportation circuit to finally acquire the key.

## Endgame Objective

After mastering various quantum gates and learning about superposition and entanglement, you'll be tasked with assembling a teleportation circuit. Successfully executing this quantum operation will grant you the key to the treasure chest. What lies inside? That's for you to find out!

## Quantum Gates

- **X Gate**: Also known as a Pauli-X gate, it flips the state of a qubit. (ALT+X)
- **Z Gate**: Known as a Pauli-Z gate, it applies a phase flip to the qubit. (ALT+Z)
- **H Gate**: Creates a superposition of two states. (ALT+H)
- **CX (Controlled Not) Gate**: Flips the target state if the control state is 1. Used to generate entanglement. (ALT+C)
- **M (Measurement) Gate**: Collapses a superposition state into a definite basis state. (ALT+M)

## Libraries Used

- Qiskit: For quantum circuit simulations.
- Arcade: For the game interface.
- NumPy: For numerical calculations.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```
git clone https://github.com/sahnawaz-live/Quanta-Quest
cd Quanta-Quest
uv sync
uv run quanta-quest
```

Or run directly:

```
uv run python -m quanta_quest
```

## Project Structure

```
Quanta-Quest/
├── src/
│   └── quanta_quest/
│       ├── __init__.py          # Package entry point
│       ├── __main__.py          # python -m support
│       ├── constants.py         # Game constants
│       ├── sprites.py           # Sprite classes (player, gates, balls)
│       ├── views.py             # Game views (menu, game, pause, game over)
│       ├── gate_manipulator.py  # Quantum gate simulation logic
│       └── assets/              # Runtime game assets (images)
├── docs/
│   ├── screenshots/             # README screenshots
│   └── videos/                  # Demo videos
├── resources/
│   ├── svg/                     # SVG source files
│   └── images/                  # Additional image resources
├── pyproject.toml
├── uv.lock
├── .gitignore
├── README.md
└── LICENSE
```

## Screenshots

![](docs/screenshots/game_first_page.png)

![](docs/screenshots/game_2nd_page.png)

## Future Steps

We are committed to leveling up the game with more advanced quantum concepts. Planned topics include quantum Fourier transformation, Shor's Algorithm, and Grover's search. We also aim to improve the graphics and add audio cues for a more immersive experience.

## Acknowledgements

I would like to acknowledge [Abhirup Mukherjee](https://abhirup-m.github.io/) for his invaluable contribution.
