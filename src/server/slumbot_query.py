import settings.constants as constants
import settings.arguments as arguments
import subprocess
import os
import sys
import utils.global_variables as global_variables

sys.path.append(os.getcwd())


def remove_last_action_from_matchstate_string(matchstate_string):
    parts = matchstate_string.split(":")
    actions = parts[3]
    previous_round = False
    start = len(actions) - 1
    if actions[-1] == "/":
        previous_round = True
        start -= 1
    i = 0
    while actions[start - i].isdigit():
        i += 1
    return_action = actions[start - i:start + 1]
    parts[3] = actions[:start - i]
    if previous_round:
        cards = parts[4]
        i = 0
        while cards[-1 - i] != "/":
            i += 1
        parts[4] = cards[:-1 - i]
    return ":".join(parts), return_action


def remove_actions_from_matchstate_string(matchstate_string, num_actions):
    action = None
    for _ in range(num_actions):
        matchstate_string, action = remove_last_action_from_matchstate_string(matchstate_string)
    return matchstate_string, action


def matchstate_string_to_slumbot_with_actions(state, actions):
    prev_pot = state.prev_pot
    matchstate_string = state.matchstate_string
    parts = matchstate_string.split(":")
    parts[1] = "0" if parts[1] == "1" else "1"
    parts[3] = ""
    if global_variables.cdbr_normal_resolve:
        current_pot = 0
        break_out = False
        for street in range(state.current_street):
            if break_out:
                break
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
            if not break_out and street != state.current_street - 1:
                parts[3] += "/"
    for action in actions:
        if action == constants.Actions.fold.value:
            parts[3] += "f"
        elif action == constants.Actions.ccall.value:
            parts[3] += "c"
        else:
            parts[3] += "b" + str(int(action - prev_pot))
    parts[3] = parts[3].replace("cc", "ck")
    parts[3] = parts[3].replace("/c", "/k")
    card_parts = parts[4].split("/")
    hands = card_parts[0].split("|")
    card_parts[0] = hands[1] + "|" + hands[0]
    parts[4] = "/".join(card_parts)
    return ":".join(parts)


def convert_matchstate_string_to_arguments(matchstate_string):
    pipe_position = matchstate_string.find("|")
    parts = []
    if matchstate_string[pipe_position - 1] == ":":
        parts.append(matchstate_string[:pipe_position + 1])
        parts.append(matchstate_string[pipe_position + 5:])
    else:
        parts.append(matchstate_string[:pipe_position - 4])
        parts.append(matchstate_string[pipe_position:])
    if parts[1] == "":
        parts[1] = "NULL"
    return parts


def query_the_strategy(args):
    return subprocess.run([arguments.path_to_query_file] + arguments.query_file_args + args, capture_output=True)


def parse_results(results):
    if results.stderr.decode(results.stderr.decode("utf-8")) != "":
        print(f"There is some error output from the C++ strategy query: {results.stderr}")
    parts = results.stdout.decode("utf-8").split()
    all_results = []
    for part in parts:
        all_results.append(parse_public_state(part))
    return all_results


def parse_public_state(strategy_string):
    actions = []
    bet = False
    for i in range(len(strategy_string)):
        if bet:
            if strategy_string[i].isdigit():
                end += 1
            else:
                actions.append(strategy_string[start:end])
                if strategy_string[i] == "b":
                    start = i
                    end = i + 1
                else:
                    actions.append(strategy_string[i:i + 1])
                    bet = False
        else:
            if strategy_string[i] == "b":
                bet = True
                start = i
                end = i + 1
            else:
                actions.append(strategy_string[i:i + 1])
    if bet:
        actions.append(strategy_string[start:end])
    assert len(
        actions) == 1326, f"Wrong number of actions in public state! ({len(actions)})"
    return actions


def get_strategy_from_slumbot(situations):
    results = query_the_strategy(
        [arg for situation in situations for arg in convert_matchstate_string_to_arguments(situation)])
    return parse_results(results)
