# client/system/control/aerator_controller.py

from system.control.relays import LoadRelay

class AeratorController:
    def __init__(self):
        self.relay = LoadRelay()
        self.logical_state = False
        self.active_idx = 0

    def turn_on(self, idx=0):
        self.relay.turn_on(idx)
        self.logical_state = True
        self.active_idx = idx

    def get_logical_state(self):
        return self.logical_state

    def get_active_index(self):
        return self.active_idx
    
    def get_logical_states(self):
        return self.relay.get_all_states()

aerator = AeratorController()
