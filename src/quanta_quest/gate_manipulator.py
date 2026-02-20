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

def gate_on_state(state_number, gate, master_number=None):
    Zgate = np.array([[1, 0], [0, -1]])
    Xgate = np.array([[0, 1], [1, 0]])
    Hgate = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    states_arr = [state0(),state1(),state2(),state3(),state4(),state5(),state6(),state7()]
    state = states_arr[state_number]
    if gate != "C":
        state = states_arr[state_number]
        gate_index = ["Z", "X", "H"].index(gate)
        final_state = np.dot([Zgate, Xgate, Hgate][gate_index], state)
        for i, known_state in enumerate(states_arr):
            if np.allclose(final_state, known_state):
                return i
    else:
        state_set = False
        if master_number in [2, 3]:
            final_state = np.dot(Xgate, state)
            state_set = True
        elif master_number > 3:
            final_state = state + np.dot(Xgate, state)
            state_set = True
        if state_set:
            final_state = final_state / np.linalg.norm(final_state)
            for i, known_state in enumerate(states_arr):
                if np.allclose(final_state, known_state):
                    return i
