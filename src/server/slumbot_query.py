import settings.constants as constants
import settings.arguments as arguments
import subprocess
import os
import sys
sys.path.append(os.getcwd())

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
                    actions.append(strategy_string[i:i+1])
                    bet = False
        else:
            if strategy_string[i] == "b":
                bet = True
                start = i
                end = i + 1
            else:
                actions.append(strategy_string[i:i+1])
    if bet:
        actions.append(strategy_string[start:end])    
    assert len(
        actions) == 1326, f"Wrong number of actions in public state! ({len(actions)})"
    return actions


def get_strategy_from_slumbot(situations):
    results = query_the_strategy(
        [arg for situation in situations for arg in convert_matchstate_string_to_arguments(situation)])
    return parse_results(results)
