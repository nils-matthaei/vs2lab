import random
import logging
import threading

# coordinator messages
from const3PC import VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT, PREPARE_COMMIT
# participant decissions
from const3PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, NEED_DECISION, READY_COMMIT
# misc constants
from const3PC import TIMEOUT

import stablelog


class Participant:
    """
    Implements a two phase commit participant.
    - state written to stable log (but recovery is not considered)
    - in case of coordinator crash, participants mutually synchronize states
    - system blocks if all participants vote commit and coordinator crashes
    - allows for partially synchronous behavior with fail-noisy crashes
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log(
            "participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.2pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state = 'NEW'
        self.decision = '' # The local decision
        self.coordinator_state = '' # Keeps track of the corrensponding states of the coordinator based on the messages received

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_ABORT if random.random() > 0.5 else LOCAL_SUCCESS #2/3

    def _enter_state(self, state, reason=''): # Overloaded for better logs
        self.stable_log.info(state)  # Write to recoverable persistant log file

        if reason != '':
            self.logger.info("Participant {} entered state {}. Reason: {}"
                         .format(self.participant, state, reason))
        else: 
            self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')  # Start in local INIT state.
        self.coordinator_state = 'INIT'

    def choose_new_coordinator(self): # select new coordinator based on smallest ID
        min_id = min(self.all_participants)
        if min_id == self.participant:
            print("I ({}) am new coordinator in state {}".format(self.participant, self.coordinator_state))
            thread = threading.Thread(target=self.run_coordinator) # Run the coordinator code in a seperate thread
            thread.start()
        self.coordinator = {str(min_id)} # Update ref to coordinator for all participants
        print("Participant {} chose new Coordinator {}".format(self.participant, min_id))

    def run(self):
        # Wait for start of joint commit
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        coordinator_msg = ''

        if not msg: # Coordinator crashed in INIT => Instant Abort
            self.decision = LOCAL_ABORT
            self._enter_state('ABORT', 'Coordinator Timeout in INIT')

            return "Participant {} terminated in state {} due to {}. (Own decision was {})".format(
                self.participant, self.state, "Coordinator crash in INIT", self.decision)

        else:
            assert msg[1] == VOTE_REQUEST
            self.coordinator_state = 'WAIT'
            self.decision = self._do_work()  # local decision

            if self.decision == LOCAL_ABORT:
                self._enter_state('ABORT', 'self.work failed')
                self.channel.send_to(self.coordinator, VOTE_ABORT)
            else:
                assert self.decision == LOCAL_SUCCESS
                self._enter_state('READY', 'self.work was success')

                self.channel.send_to(self.coordinator, VOTE_COMMIT)

                print("Participant {} sending VOTE COMMIT".format(self.participant))

        #Listen for next msg from coodinator
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:  # Crashed coordinator
            print("Participant {}[READY]: Coordinator crash detected".format(self.participant))
            self.choose_new_coordinator() #select and start a new coordinator
            coordinator_msg = self.handle_new_coordinator() # Receive state and decision of new coordinator. Also adjusts local state

            return "Participant {} terminated in state {} due to {}. (Own decision was {})".format( #There will be an absolut decision by the new coordinator so we can terminate here
            self.participant, self.state, coordinator_msg, self.decision)

        else:
            coordinator_msg = msg[1]

        #regular precommit phase
        if coordinator_msg == PREPARE_COMMIT:
            self._enter_state('PRECOMMIT')
            self.coordinator_state = 'PRECOMMIT'
            self.channel.send_to(self.coordinator, READY_COMMIT)

        else:
            assert (coordinator_msg == GLOBAL_ABORT  or self.decision == LOCAL_ABORT)
            self.coordinator_state = 'ABORT'
            self._enter_state('ABORT')

            if coordinator_msg == GLOBAL_ABORT:
                return "Participant {} terminated in state {} due to {}. (Own decision was {})".format(
                self.participant, self.state, coordinator_msg, self.decision)

        # Receive next msg from coordinator
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg: #Coordinator crash
            print("Participant {}[PRECOMMIT]: Coordinator crash detected".format(self.participant))
            self.choose_new_coordinator()
            coordinator_msg = self.handle_new_coordinator()
        else:
            coordinator_msg = msg[1]

        # finally set the state according to the last msg and terminate
        if coordinator_msg == GLOBAL_COMMIT and self.state != 'COMMIT':
            self._enter_state('COMMIT')
        elif coordinator_msg == GLOBAL_ABORT and self.state != 'ABORT':
            self._enter_state('ABORT')

        return "Participant {} terminated in state {} due to {}. (Own decision was {})".format(
            self.participant, self.state, coordinator_msg, self.decision)
    
    def handle_new_coordinator(self):
        msg = self.channel.receive_from(self.coordinator, TIMEOUT) # Wait for new coordinator to announce its state
        new_coord_state = msg[1]
        self.coordinator_state = new_coord_state

        # In my understanding, these are the only two states worth handling here
        if new_coord_state == 'ABORT':
            self._enter_state('ABORT', 'New coordinator has communicated ABORT')
            return
        elif new_coord_state == 'COMMIT':
            self._enter_state('COMMIT', 'New coordinator has communicated COMMIT')
            return
        
        # Coordinator state was not ABORT or COMMIT, so we wait for its decision
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        coordinator_msg = msg[1]
        
        # apply the new coordinators decision
        if coordinator_msg == GLOBAL_ABORT:
            self._enter_state('ABORT')
        else:
            assert coordinator_msg == GLOBAL_COMMIT
            self._enter_state('COMMIT')

        return coordinator_msg
    
    
    def run_coordinator(self):
        self.channel.send_to(self.all_participants, self.coordinator_state) # Announce new state

        if self.coordinator_state == 'WAIT': # If p_k is in state wait, it sends GLOBAL_ABORT
            self.coordinator_state == 'ABORT'
            self.channel.send_to(self.all_participants, GLOBAL_ABORT)
        elif self.coordinator_state == 'PRECOMMIT': # If p_k is in state PRECOMMIT it sends GLOBAL_COMMIT
            self.coordinator_state = 'COMMIT'
            self.channel.send_to(self.all_participants, GLOBAL_COMMIT)
        else:
            assert(self.coordinator_state == 'COMMIT' or self.coordinator_state == 'ABORT') #If p_k is in these states, the logic in handle_new_coordinator should suffice to handle the termination

    #🍝
