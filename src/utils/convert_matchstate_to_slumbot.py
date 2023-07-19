from server.protocol_to_node import parse_state
import settings.constants as constants


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


if __name__ == '__main__':
    matchstate = parse_state("MATCHSTATE:1:51:cr300r900c/cr2700c/r5400r16200c/c:|4s8h/6d9hJs/6s/8s")
    print(get_matchstate_string(matchstate))
