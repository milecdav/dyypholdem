import os
import sys
sys.path.append(os.getcwd())

import subprocess
import settings.arguments as arguments
import settings.constants as constants



situations = [
    "MATCHSTATE:0:0:b433:AsQs|",
    "MATCHSTATE:0:0:b300c/kk/b300b1800c/kb5400:3s3h|/Qs6s4h/3c/Jd",
    "MATCHSTATE:0:0:b300c/kk/b300b1800c/kb5400:5s2h|/Qs6s4h/3c/Jd",
    "MATCHSTATE:1:0::|7h2c",
    "MATCHSTATE:1:0::|9h8h",
    "MATCHSTATE:1:0:b200c/kk/b400:|5s2h/Qs6s4h/3c",
    "MATCHSTATE:1:0:b200c/kk/b400c/k:|5s2h/Qs6s4h/3c/Kh",
]

real_situations = ['MATCHSTATE:1:0::|7d7c', 'MATCHSTATE:1:0:cb200:|7d7c', 'MATCHSTATE:1:0:cb200b600b1800:|7d7c', 'MATCHSTATE:1:0:cb200b600b1800b5400b16200:|7d7c', 'MATCHSTATE:1:0:cb200b600b1800b5400b20000:|7d7c', 'MATCHSTATE:1:0:cb200b600b20000:|7d7c', 'MATCHSTATE:1:0:cb20000:|7d7c', 'MATCHSTATE:1:0:b200b600:|7d7c', 'MATCHSTATE:1:0:b200b600b1800b5400:|7d7c', 'MATCHSTATE:1:0:b200b600b1800b5400b16200b20000:|7d7c', 'MATCHSTATE:1:0:b200b600b1800b20000:|7d7c', 'MATCHSTATE:1:0:b200b20000:|7d7c']


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
    print(parts)
    return parts


def query_the_strategy(args):
    return subprocess.run([arguments.path_to_query_file] + arguments.query_file_args + args, capture_output=True)


def parse_results(results):
    assert results.stderr.decode(
        "utf-8") == "", f"There is some error output from the C++ strategy query: {results.stderr}"
    parts = results.stdout.decode("utf-8").split()
    for part in parts:
        parse_public_state(part)


def parse_public_state(strategy_string):
    actions = []
    bet = False
    print(strategy_string)
    print(len(strategy_string))
    print(strategy_string.count("1"))
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
    print(actions)


if __name__ == "__main__":
    results = query_the_strategy(
        [arg for situation in real_situations for arg in convert_matchstate_string_to_arguments(situation)])
    parse_results(results)
