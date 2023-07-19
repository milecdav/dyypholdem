import os
import sys
import argparse
import numpy as np
import string

sys.path.append(os.getcwd())

import server.slumbot_query as slumbot_query



def get_matchstate_string(state):     
    matchstate_string = state.matchstate_string.strip()
    parts = matchstate_string.split(":")    
    parts[3] = ""                          
    current_pot = 0
    for street in range(state.current_street):                
        immediate_pot = 100
        for action in state.actions[street]:
            if action.action == constants.ACPCActions.ccall:                        
                parts[3] += "c"
            elif action.action == constants.ACPCActions.rraise:
                parts[3] += "b" + str(action.raise_amount - current_pot)
                immediate_pot = action.raise_amount
            else:
                assert False, "We should not be in terminal node"
        current_pot = max(immediate_pot, current_pot)
        if street != state.current_street - 1:
            parts[3] += "/"
    parts[3] = parts[3].replace("cc", "ck")
    parts[3] = parts[3].replace("/c", "/k")    
    return ":".join(parts)


def run(server, port):
    # 1.0 connecting to the server
    acpc_game = ACPCGame()
    acpc_game.connect(server, port)

    state: ProcessedState
    winnings = 0
    hands = 0

    # 2.0 main loop that waits for a situation where we act and then chooses an action
    while True:
        # 2.1 blocks until it's our situation/turn
        state, node, hand_winnings = acpc_game.get_next_situation()

        if state is None:
            # game ended or connection to server broke
            break

        if node is not None:
            matchstate_string = get_matchstate_string(state)

            strategy = slumbot_query.get_strategy_from_slumbot([matchstate_string])[0]

            action = strategy[state.hand_id]

            if action.startswith("b"):
                action = int(action.strip("b")) + state.prev_pot
            
            if action == "f":
                acpc_action = Action(action=constants.ACPCActions.fold)
            elif action == "c":
                acpc_action = Action(action=constants.ACPCActions.ccall, raise_amount=abs(state.bet1 - state.bet2))
            else:                
                acpc_action = Action(action=constants.ACPCActions.rraise, raise_amount=action)

            # 2.3 send the action to the dealer
            acpc_game.play_action(acpc_action)
        else:
            # hand has ended
            winnings += hand_winnings
            hands += 1
            arguments.logger.success(f"Hand completed. Hand winnings: {hand_winnings}, Total winnings: {winnings} in hand {hands}")

    arguments.logger.success(f"Game ended >>> Total winnings: {winnings}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Play poker on an ACPC server')
    parser.add_argument('hostname', type=str, help="Hostname/IP of the server running ACPC dealer")
    parser.add_argument('port', type=int, help="Port to connect on the ACPC server")
    args = parser.parse_args()

    import settings.arguments as arguments
    import settings.constants as constants

    from server.acpc_game import ACPCGame
    from server.protocol_to_node import Action, ProcessedState

    np.random.seed(0)

    arguments.logger.remove(1)

    run(args.hostname, args.port)
