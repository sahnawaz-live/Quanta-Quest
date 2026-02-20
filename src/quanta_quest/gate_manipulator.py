"""Quantum gate simulation for Quanta Quest."""

import random

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def state0():
    qc = QuantumCircuit(1)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state1():
    qc = QuantumCircuit(1)
    qc.x(0); qc.z(0); qc.x(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state2():
    qc = QuantumCircuit(1)
    qc.x(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state3():
    qc = QuantumCircuit(1)
    qc.x(0); qc.z(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state4():
    qc = QuantumCircuit(1)
    qc.h(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state5():
    qc = QuantumCircuit(1)
    qc.x(0); qc.h(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state6():
    qc = QuantumCircuit(1)
    qc.x(0); qc.h(0); qc.x(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)

def state7():
    qc = QuantumCircuit(1)
    qc.h(0); qc.z(0); qc.x(0); qc.z(0)
    statevector = Statevector.from_instruction(qc)
    return np.array(statevector.data)


# Precompute all states once
_STATES = None

def _get_states():
    global _STATES
    if _STATES is None:
        _STATES = [state0(), state1(), state2(), state3(),
                    state4(), state5(), state6(), state7()]
    return _STATES


# Gate matrices
_Zgate = np.array([[1, 0], [0, -1]])
_Xgate = np.array([[0, 1], [1, 0]])
_Hgate = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
_Sgate = np.array([[1, 0], [0, 1j]])


def gate_on_state(state_number, gate, master_number=None):
    """Apply a quantum gate to a state and return the resulting state index."""
    states_arr = _get_states()
    state = states_arr[state_number]
    if gate == "C":
        return _apply_cnot(state, state_number, master_number, states_arr)
    else:
        gate_map = {"Z": _Zgate, "X": _Xgate, "H": _Hgate, "S": _Sgate}
        gate_matrix = gate_map.get(gate)
        if gate_matrix is None:
            return state_number
        final_state = np.dot(gate_matrix, state)
        for i, known_state in enumerate(states_arr):
            if np.allclose(final_state, known_state):
                return i
        return state_number


def _apply_cnot(state, state_number, master_number, states_arr):
    """Apply CNOT gate based on master qubit state."""
    state_set = False
    if master_number in [2, 3]:
        final_state = np.dot(_Xgate, state)
        state_set = True
    elif master_number is not None and master_number > 3:
        final_state = state + np.dot(_Xgate, state)
        state_set = True
    if state_set:
        norm = np.linalg.norm(final_state)
        if norm > 1e-10:
            final_state = final_state / norm
        for i, known_state in enumerate(states_arr):
            if np.allclose(final_state, known_state):
                return i
    return state_number


def measure_state(state_number):
    """Measure a quantum state, collapsing superposition to a basis state.

    Returns the collapsed state index:
    - States 0, 1 (|0⟩ variants) → remain as-is (already definite)
    - States 2, 3 (|1⟩ variants) → remain as-is (already definite)
    - States 4-7 (superpositions) → collapse to 0 or 2 with appropriate probability
    """
    if state_number in [0, 1]:
        return 0  # Already |0⟩
    elif state_number in [2, 3]:
        return 2  # Already |1⟩
    else:
        # Superposition state: compute probability of |0⟩
        states_arr = _get_states()
        state = states_arr[state_number]
        prob_zero = abs(state[0]) ** 2
        if random.random() < prob_zero:
            return 0  # Collapsed to |0⟩
        else:
            return 2  # Collapsed to |1⟩


def is_superposition(state_number):
    """Check if a state is in superposition (not a definite basis state)."""
    return state_number >= 4


def is_entangled_pair(state1_number, state2_number):
    """Check if two states form an entangled-like pair (both in superposition)."""
    return is_superposition(state1_number) and is_superposition(state2_number)
