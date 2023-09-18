import os
import sys
import argparse

sys.path.append(os.getcwd())
from utils.log_to_file import log_line
from utils import global_variables

import settings.arguments as arguments
import game.card_tools as card_tools

last_state = None
last_node = None


def run(server, port):
    global last_state
    global last_node

    # 1.0 connecting to the server
    acpc_game = ACPCGame()
    acpc_game.connect(server, port)

    current_state: protocol_to_node.ProcessedState
    current_node: TreeNode

    winnings = 0
    hand = 0

    # 2.0 main loop that waits for a situation where we act and then chooses an action
    while True:

        # 2.1 blocks until it's our situation/turn
        current_state, current_node, hand_winnings = acpc_game.get_next_situation_for_cdbr_vs_cdbr()

        if current_state is None:
            # game ended or connection to server broke
            break

        bot_player = current_state.player

        if current_node is not None:
            # do we have a new hand?
            if last_state is None or last_state.hand_number != current_state.hand_number or current_node.street < last_node.street:
                arguments.logger.trace(
                    f"Initiating garbage collection. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")
                last_node = None
                last_state = None
                gc.collect()
                if arguments.use_gpu:
                    torch.cuda.empty_cache()
                    arguments.logger.trace(
                        f"Garbage collection completed. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")
                continual_resolving.start_new_hand(current_state)

            # 2.1 use continual resolving to find a strategy and make an action in the current node
            if last_state is None:
                if current_state.acting_player == bot_player:
                    continual_resolving.only_resolve(current_state, current_node)
            else:
                if last_state.acting_player == bot_player and current_state.acting_player == bot_player:
                    global_variables.cdbr_opponent_range = card_tools.normalize_range(current_node.board, global_variables.cdbr_opponent_range)
                    continual_resolving.only_resolve(current_state, current_node)
                elif last_state.acting_player != bot_player and current_state.acting_player == bot_player:
                    continual_resolving.only_update_opponent_range(current_state, current_node)
                    continual_resolving.only_resolve(current_state, current_node)
                elif last_state.acting_player != bot_player and current_state.acting_player != bot_player:
                    continual_resolving.only_update_opponent_range(current_state, current_node)
                else:
                    # doing nothing
                    arguments.logger.trace("State in which we do nothing.")
                    if global_variables.cdbr_exploited:
                        continual_resolving.only_resolve(current_state, current_node)

            global_variables.cdbr_exploiter_prev_node = current_node

            if current_state.acting_player == bot_player:
                advised_action: protocol_to_node.Action = continual_resolving.only_sample_action(current_state, current_node)

                if advised_action.action == constants.ACPCActions.ccall:
                    advised_action.raise_amount = abs(current_state.bet1 - current_state.bet2)

                # 2.2 send the action to the dealer
                acpc_game.play_action(advised_action)

            last_state = current_state
            last_node = current_node

            # force clean up
            arguments.logger.trace(
                f"Initiating garbage collection. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")
            gc.collect()
            if arguments.use_gpu:
                torch.cuda.empty_cache()
                arguments.logger.trace(
                    f"Garbage collection completed. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")
        else:
            winnings += hand_winnings
            arguments.logger.success(f"Hand completed. Hand winnings: {hand_winnings}, Total winnings: {winnings} in hand {hand}")
            if args.log:
                log_line(f"{hand} {hand_winnings} {winnings}", args.log)
            hand += 1

    arguments.logger.success(f"Game ended >>> Total winnings: {winnings}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Play poker on an ACPC server')
    parser.add_argument('hostname', type=str, help="Hostname/IP of the server running ACPC dealer")
    parser.add_argument('port', type=int, help="Port to connect on the ACPC server")
    parser.add_argument('--log', type=str, help="Log file name")
    parser.add_argument('--exploited', help="Whether to export the strategy for exploitation", action="store_true")
    parser.add_argument('--exploiter', help="Whether to use the exported strategy", action="store_true")
    parser.add_argument('--id', type=str, help="ID for file exchange")
    args = parser.parse_args()

    if args.exploited or args.exploiter:
        global_variables.cdbr_exploitation_id = args.id

    if args.exploited:
        global_variables.cdbr_exploited = True
        with open(arguments.cdbr_ready_path.format(global_variables.cdbr_exploitation_id), 'w') as handle:
            handle.write("0")

    if args.exploiter:
        global_variables.cdbr_exploiter = True

    import gc

    import torch

    import settings.arguments as arguments
    import settings.constants as constants

    from server.acpc_game import ACPCGame
    import server.protocol_to_node as protocol_to_node
    from tree.tree_node import TreeNode
    from lookahead.continual_resolving import ContinualResolving

    import utils.pseudo_random as random_

    continual_resolving = ContinualResolving()

    if arguments.use_pseudo_random:
        random_.manual_seed(0)

    run(args.hostname, args.port)
