import os
import sys
import argparse
from multiprocessing import Pool

sys.path.append(os.getcwd())

import gc

import torch

import settings.arguments as arguments

from server.slumbot_game import SlumbotGame
import server.protocol_to_node as protocol_to_node
from lookahead.continual_resolving import ContinualResolving

import settings.constants as constants
from server.protocol_to_node import Action, ProcessedState

import numpy as np

from utils.log_to_file import log_line


def play_hand(token, hand, slumbot_game, continual_resolving):
    failed = False

    response = slumbot_game.new_hand(token)
    new_token = response.get('token')
    if new_token:
        token = new_token
    arguments.logger.trace(f"Current token: {token}")

    current_state, current_node = slumbot_game.get_next_situation(response)

    winnings = response.get('winnings')
    # game goes on
    if winnings is None:

        arguments.logger.info(f"Starting new hand #{hand + 1}")
        continual_resolving.start_new_hand(current_state)

        while True:
            # use continual resolving to find a strategy and make an action in the current node
            try:
                advised_action: protocol_to_node.Action = continual_resolving.compute_action(current_state, current_node)
            except:
                failed = True
                if current_state.bet1 == current_state.bet2:
                    advised_action = Action(action=constants.ACPCActions.ccall, raise_amount=abs(current_state.bet1 - current_state.bet2))
                else:
                    advised_action = Action(action=constants.ACPCActions.fold)
            # send the action to the server
            response = slumbot_game.play_action(token, advised_action)
            current_state, current_node = slumbot_game.get_next_situation(response)

            winnings = response.get('winnings')
            if winnings is not None:
                # hand has ended
                break

    # clean up and release memory
    if arguments.use_gpu:
        arguments.logger.trace(f"Initiating garbage collection. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")
    del current_node
    del current_state
    gc.collect()
    if arguments.use_gpu:
        torch.cuda.empty_cache()
        arguments.logger.trace(f"Garbage collection performed. Allocated memory={torch.cuda.memory_allocated('cuda')}, Reserved memory={torch.cuda.memory_reserved('cuda')}")

    return token, winnings, failed


def play_slumbot(num_hands):
    slumbot_game = SlumbotGame()
    token = check_credentials(slumbot_game)
    continual_resolving = ContinualResolving()
    winnings = 0
    failed = 0
    for hand in range(num_hands):
        token, hand_winnings, hand_failed = play_hand(token, hand, slumbot_game, continual_resolving)
        winnings += hand_winnings
        if args.log:
            log_line(f"{hand} {winnings}", args.log)
        if hand_failed:
            failed += 1
            arguments.logger.error(f"Bot crashed. Game was completed as always fold.")
        arguments.logger.success(f"Hand completed. Hand winnings: {hand_winnings}, Total winnings: {winnings} in hand {hand}")

    arguments.logger.success(f"Game ended >>> Total winnings: {winnings}")
    arguments.logger.success(f"Total crashes: {failed}")
    return winnings


def check_credentials(slumbot_game):
    token = slumbot_game.login(arguments.slumbot_username, arguments.slumbot_password)
    if token is None:
        arguments.logger.error("Login failed.")
        sys.exit(1)
    else:
        arguments.logger.success("Login successful.")
    return token


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play with DyypHoldem against Slumbot')
    parser.add_argument('hands', type=int, help="Number of hands to play against Slumbot")
    parser.add_argument('--multithread', type=int, help="Number of games to play in parallel")
    parser.add_argument('--log', type=str, help="Log file name")
    args = parser.parse_args()

    if args.log:
        arguments.logger.success("Logging to file: " + args.log + " in directory " + os.getcwd())

    if args.multithread:
        num_hands_array = np.full(args.multithread, fill_value=int(args.hands / args.multithread), dtype=int)
        i = 0
        while np.sum(num_hands_array) < args.hands:
            num_hands_array[i] += 1
            i += 1
        all_winnings = Pool(args.multithread).map(play_slumbot, num_hands_array)
        arguments.logger.success(f"Experiment ended >>> All the winnings: {all_winnings}")
    else:
        play_slumbot(args.hands)
