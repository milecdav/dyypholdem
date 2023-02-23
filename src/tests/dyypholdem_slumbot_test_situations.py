import os
import sys
from lookahead.continual_resolving import ContinualResolving
import settings.constants as constants

sys.path.append(os.getcwd())

last_state = None
last_node = None
continual_resolving = ContinualResolving()

game_hands = [
    [
        {'old_action': '', 'action': 'b200', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': []},
        {'old_action': 'b200', 'action': 'b200b600b1800', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': []},
        {'old_action': 'b200b600b1800', 'action': 'b200b600b1800c/', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': ['As', 'Qc', '4s']},
        {'old_action': 'b200b600b1800c/', 'action': 'b200b600b1800c/kb1800', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': ['As', 'Qc', '4s']},
        {'old_action': 'b200b600b1800c/kb1800', 'action': 'b200b600b1800c/kb1800c/', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': ['As', 'Qc', '4s', '9c']},
        {'old_action': 'b200b600b1800c/kb1800c/', 'action': 'b200b600b1800c/kb1800c/kb7200', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': ['As', 'Qc', '4s', '9c']},
        {'old_action': 'b200b600b1800c/kb1800c/kb7200', 'action': 'b200b600b1800c/kb1800c/kb7200c/', 'client_pos': 0, 'hole_cards': ['Jc', 'Tc'], 'board': ['As', 'Qc', '4s', '9c', '7c']},
    ],
    [
        {'old_action': '', 'action': 'b200', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': []},
        {'old_action': 'b200', 'action': 'b200b600b1800', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': []},
        {'old_action': 'b200b600b1800', 'action': 'b200b600b1800c/', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': ['9h', '6s', '5c']},
        {'old_action': 'b200b600b1800c/', 'action': 'b200b600b1800c/kb1800', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': ['9h', '6s', '5c']},
        {'old_action': 'b200b600b1800c/kb1800', 'action': 'b200b600b1800c/kb1800c/', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': ['9h', '6s', '5c', 'Ts']},
        {'old_action': 'b200b600b1800c/kb1800c/', 'action': 'b200b600b1800c/kb1800c/kb3600', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': ['9h', '6s', '5c', 'Ts']},
        {'old_action': 'b200b600b1800c/kb1800c/kb3600', 'action': 'b200b600b1800c/kb1800c/kb3600b15800b16400', 'client_pos': 0, 'hole_cards': ['5h', '5d'], 'board': ['9h', '6s', '5c', 'Ts']}
    ]
]


def replay():
    for hand in game_hands:
        for message in hand:
            run(message)


def run(msg):
    global last_state
    global last_node
    # global continual_resolving

    # parse the state message
    current_state, current_node, winnings = get_state(msg)

    if msg.get('old_action') == "":
        continual_resolving.start_new_hand(current_state)

    # do we have a new hand?
    if winnings:
        print(f"Hand ended with winnings: {winnings}")
    # use continual resolving to find a strategy and make an action in the current node
    advised_action: protocol_to_node.Action = continual_resolving.compute_action(current_state, current_node)

    last_state = current_state
    last_node = current_node

    # force clean up
    if arguments.use_gpu:
        arguments.logger.trace(
            f"Initiating garbage collection. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")
    gc.collect()
    if arguments.use_gpu:
        torch.cuda.empty_cache()
        arguments.logger.trace(f"Garbage collection performed. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")


def get_state(msg):
    arguments.logger.info(f"Received Slumbot message: {msg}")

    # 2.0 parse the string to our state representation
    current_state, current_node = slumbot_game.get_next_situation(msg)
    arguments.logger.debug(current_state)

    winnings = msg.get('winnings')
    # game goes on
    return current_state, current_node, winnings


if __name__ == "__main__":
    import gc

    import torch

    import settings.arguments as arguments

    import server.protocol_to_node as protocol_to_node
    from server.slumbot_game import SlumbotGame

    import utils.pseudo_random as random_

    random_.manual_seed(0)

    slumbot_game = SlumbotGame()

    slumbot_game.last_response = None
    slumbot_game.acpc_actions = ""
    slumbot_game.max_bet = 0
    slumbot_game.bet_this_street = 0
    slumbot_game.bet_previous_streets = 0
    slumbot_game.current_street = 0

    arguments.logger.info("Running test")
    random_.manual_seed(0)
    replay()
    arguments.logger.success("Test completed")
