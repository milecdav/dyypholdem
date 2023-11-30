import settings.arguments as arguments
import settings.constants as constants
import settings.game_settings as game_settings

import utils.global_variables as global_variables

import game.card_tools as card_tools


class StrategyFilling(object):

    def __init__(self):
        pass

    # --- Fills a public tree with a uniform strategy.
    # -- @param tree a public tree for Leduc Hold'em or variant
    def fill_strategy(self, tree):
        self._fill_strategy_dfs(tree)

    # --- Fills a node with a uniform strategy and recurses on the children.
    # -- @param node the node
    # -- @local
    def _fill_strategy_dfs(self, node):
        if node.current_player == constants.Players.Chance:
            self._fill_chance(node)
        else:
            self._fill_strategy(node)

        for i in range(0, len(node.children)):
            self._fill_strategy_dfs(node.children[i])

    # --- Fills a chance node with the probability of each outcome.
    # -- @param node the chance node
    # -- @local
    @staticmethod
    def _fill_chance(node):
        assert not node.terminal

        node.strategy = arguments.Tensor(len(node.children), game_settings.hand_count).fill_(0)
        # setting probability of impossible hands to 0
        for i in range(0, len(node.children)):
            child_node = node.children[i]
            mask = card_tools.get_possible_hand_indexes(child_node.board).byte()
            node.strategy[i].fill_(0)
            # remove 4 as in Hold'em each player holds one card
            node.strategy[i][mask] = 1.0 / (game_settings.card_count - 4)

    # --- Fills a player node with a uniform strategy.
    # -- @param node the player node
    # -- @local
    @staticmethod
    def convert_action(action):
        if action == "f":
            return -2
        if action == "c":
            return -1
        if action.startswith("b"):
            action = int(action.strip("b"))
            return action + global_variables.cdbr_state.prev_pot
        assert False, "Wrong action"

    @staticmethod
    def action_to_closest_index(action_to_index, action):
        if action in action_to_index:
            return action_to_index[action]
        dist = 20000
        best_key = -3
        for key in action_to_index:
            if abs(key - action) < dist:
                best_key = key
                dist = abs(key - action)
        return action_to_index[best_key]

    def _fill_strategy(self, node):
        assert node.current_player == constants.Players.P1 or node.current_player == constants.Players.P2

        if not node.terminal:
            node.strategy = arguments.Tensor(len(node.children), game_settings.hand_count).fill_(0.0)
            if arguments.cdbr:
                if arguments.cdbr_type == constants.OpponentType.uniform_random:
                    node.strategy.fill_(1.0 / len(node.children))
                elif arguments.cdbr_type == constants.OpponentType.always_fold:
                    node.strategy[0, :] = 1.0
                elif arguments.cdbr_type == constants.OpponentType.always_call:
                    node.strategy[1, :] = 1.0
                elif arguments.cdbr_type == constants.OpponentType.slumbot:
                    if node.id in global_variables.cdbr_node_to_index:
                        results = global_variables.cdbr_query_results[global_variables.cdbr_node_to_index[node.id]]
                        if results[0] == "e":
                            arguments.logger.trace(f"Error from query for matchstate {global_variables.cdbr_query_strings[global_variables.cdbr_node_to_index[node.id]]}")
                            node.strategy[1, :] = 1.0
                        else:
                            action_to_index = {}
                            for index, action in enumerate(node.actions.cpu().numpy()):
                                action = int(action)
                                action_to_index[action] = index
                                # print(action_to_index)
                            # print(global_variables.cdbr_query_strings[global_variables.cdbr_node_to_index[node.id]])
                            for i, value in enumerate([self.action_to_closest_index(action_to_index, self.convert_action(a)) for a in results]):
                                node.strategy[value, i] = 1.0
