from typing import List
import copy
import numpy as np

import settings.arguments as arguments
import settings.constants as constants
import settings.game_settings as game_settings

import server.slumbot_query as slumbot_query

import utils.global_variables as global_variables

from tree.tree_node import TreeNode, BuildTreeParams
from tree.strategy_filling import StrategyFilling
from game.bet_sizing import BetSizing


class PokerTreeBuilder(object):
    bet_sizing: BetSizing
    limit_to_street: bool

    def __int__(self):
        pass

    # --- Fills in additional convenience attributes which only depend on existing
    # -- node attributes.
    # -- @param node the node
    # -- @local
    @staticmethod
    def _fill_additional_attributes(node: TreeNode):
        node.pot = node.bets.min()

    # --- Creates the children nodes after a chance node.
    # -- @param parent_node the chance node
    # -- @return a list of children nodes
    # -- @local
    def _get_children_nodes_chance_node(self, parent_node):
        assert parent_node.current_player == constants.Players.Chance

        if self.limit_to_street:
            return []

        # currently not supported
        raise NotImplementedError()

    # --- Creates the children nodes after a player node.
    # -- @param parent_node the chance node
    # -- @return a list of children nodes
    # -- @local
    def _get_children_nodes_player_node(self, parent_node):
        children = []

        # Action 1: fold
        # if (not parent_node.terminal) and (parent_node.bets[0].item() != parent_node.bets[1].item()):
        fold_node = TreeNode()
        fold_node.type = constants.NodeTypes.terminal_fold
        fold_node.terminal = True
        fold_node.current_player = constants.Players(
            1 - parent_node.current_player.value)
        fold_node.street = parent_node.street
        fold_node.board = parent_node.board
        fold_node.board_string = parent_node.board_string
        fold_node.bets = parent_node.bets.clone()
        children.append(fold_node)

        # Action 2: check/call
        if ((parent_node.street == 1 and parent_node.current_player == constants.Players.P1 and parent_node.num_bets == 1 and parent_node.bets[constants.Players.P2.value].item() == game_settings.big_blind) or
                ((parent_node.street != 1 or constants.streets_count == 1) and
                 parent_node.current_player == constants.Players.P2 and parent_node.bets[0].item() == parent_node.bets[1].item())):
            check_node = TreeNode()
            check_node.type = constants.NodeTypes.inner_check
            check_node.terminal = False
            check_node.current_player = constants.Players(
                1 - parent_node.current_player.value)
            check_node.street = parent_node.street
            check_node.board = parent_node.board
            check_node.board_string = parent_node.board_string
            check_node.bets = parent_node.bets.clone().fill_(parent_node.bets.max())
            check_node.num_bets = parent_node.num_bets
            children.append(check_node)
        elif (parent_node.street != constants.streets_count and
              ((parent_node.bets[0] == parent_node.bets[1] and ((parent_node.street == 1 and parent_node.current_player == constants.Players.P2) or
                                                                (parent_node.street != 1 and parent_node.current_player == constants.Players.P1))) or
               (parent_node.bets[0] != parent_node.bets[1] and parent_node.bets.max() < game_settings.stack))):
            chance_node = TreeNode()
            chance_node.type = constants.NodeTypes.chance_node
            chance_node.street = parent_node.street
            chance_node.board = parent_node.board
            chance_node.board_string = parent_node.board_string
            chance_node.current_player = constants.Players.Chance
            chance_node.bets = parent_node.bets.clone().fill_(parent_node.bets.max())
            chance_node.num_bets = 0
            children.append(chance_node)
        else:
            terminal_call_node = TreeNode()
            terminal_call_node.type = constants.NodeTypes.terminal_call
            terminal_call_node.terminal = True
            terminal_call_node.current_player = constants.Players(
                1 - parent_node.current_player.value)
            terminal_call_node.street = parent_node.street
            terminal_call_node.board = parent_node.board
            terminal_call_node.board_string = parent_node.board_string
            terminal_call_node.bets = parent_node.bets.clone().fill_(parent_node.bets.max())
            children.append(terminal_call_node)

        # Action 3: bet
        possible_bets = self.bet_sizing.get_possible_bets(parent_node)
        if possible_bets.dim() != 0:
            assert (possible_bets.size(1) == 2)
            for i in range(0, possible_bets.size(0)):
                bet_node = TreeNode()
                bet_node.parent = parent_node
                bet_node.type = constants.NodeTypes.inner_raise
                bet_node.current_player = constants.Players(
                    1 - parent_node.current_player.value)
                bet_node.street = parent_node.street
                bet_node.board = parent_node.board
                bet_node.board_string = parent_node.board_string
                bet_node.bets = possible_bets[i]
                children.append(bet_node)

        return children

    # --- Creates the children after a node.
    # -- @param parent_node the node to create children for
    # -- @return a list of children nodes
    # -- @local
    def _get_children_nodes(self, parent_node) -> List[TreeNode]:
        chance_node = parent_node.current_player == constants.Players.Chance
        # transition call -> create a chance node
        if parent_node.terminal:
            return []
        # chance node
        elif chance_node:
            return self._get_children_nodes_chance_node(parent_node)
        # inner nodes -> handle bet sizes
        else:
            return self._get_children_nodes_player_node(parent_node)

    # --- Recursively build the (sub)tree rooted at the current node.
    # -- @param current_node the root to build the (sub)tree from
    # -- @return `current_node` after the (sub)tree has been built
    # -- @local
    def put_matchstate_string_to_query(self, actions):
        state = global_variables.cdbr_state
        prev_pot = state.prev_pot        
        matchstate_string = state.matchstate_string
        parts = matchstate_string.split(":")
        parts[1] = "0" if parts[1] == "1" else "1"
        parts[3] = ""        
        if global_variables.cdbr_normal_resolve:                    
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
        global_variables.cdbr_query_strings.append(":".join(parts))

    def _build_tree_dfs(self, current_node, actions):      

        current_node.id = global_variables.max_id
        global_variables.max_id += 1        

        if arguments.cdbr and arguments.cdbr_type == constants.CDBRType.slumbot:
            if not current_node.terminal and current_node.current_player != global_variables.cdbr_player and current_node.current_player != constants.Players.Chance:
                self.put_matchstate_string_to_query(actions)
                global_variables.cdbr_node_to_index[current_node.id] = len(
                    global_variables.cdbr_query_strings) - 1

        self._fill_additional_attributes(current_node)
        children = self._get_children_nodes(current_node)
        current_node.children = children

        depth = 0

        current_node.actions = arguments.Tensor(len(children))
        for i in range(0, len(children)):
            children[i].parent = current_node
            if i == 0:
                current_action = constants.Actions.fold.value
            elif i == 1:
                current_action = constants.Actions.ccall.value
            else:
                current_action = children[i].bets.max().item()

            current_node.actions[i] = current_action
            actions_copy = copy.deepcopy(actions)
            actions_copy.append(current_action)
            self._build_tree_dfs(children[i], actions_copy)
            depth = max(depth, children[i].depth)

        current_node.depth = depth + 1

        return current_node

    # --- Builds the tree.
    # -- @param params table of tree parameters, containing the following fields:
    # --
    # -- * `street`: the betting round of the root node
    # --
    # -- * `bets`: the number of chips committed at the root node by each player
    # --
    # -- * `current_player`: the acting player at the root node
    # --
    # -- * `board`: a possibly empty vector of board cards at the root node
    # --
    # -- * `limit_to_street`: if `true`, only build the current betting round
    # --
    # -- * `bet_sizing` (optional): a @{bet_sizing} object which gives the allowed
    # -- bets for each player
    # -- @return the root node of the built tree
    def build_tree(self, build_tree_params: BuildTreeParams):
        root = TreeNode()
        root.street = build_tree_params.root_node.street
        root.board = build_tree_params.root_node.board.clone()
        root.board_string = build_tree_params.root_node.board_string
        root.current_player = build_tree_params.root_node.current_player
        root.bets = build_tree_params.root_node.bets.clone()
        root.num_bets = build_tree_params.root_node.num_bets
        root.type = constants.NodeTypes.root_node

        root.bet_sizing = build_tree_params.bet_sizing or BetSizing(
            game_settings.bet_sizing)
        assert root.bet_sizing, "no bet sizes defined"
        self.bet_sizing = root.bet_sizing
        self.limit_to_street = build_tree_params.limit_to_street
        if arguments.cdbr and arguments.cdbr_type == constants.CDBRType.slumbot:
            global_variables.cdbr_query_strings = []
            global_variables.cdbr_node_to_index = {}

        global_variables.max_id = 0

        self._build_tree_dfs(root, [])

        # print(global_variables.cdbr_state.matchstate_string)

        # print(global_variables.cdbr_query_strings)
        if arguments.cdbr and arguments.cdbr_type == constants.CDBRType.slumbot:
            global_variables.cdbr_query_results = slumbot_query.get_strategy_from_slumbot(global_variables.cdbr_query_strings)

        strategy_filling = StrategyFilling()
        strategy_filling.fill_strategy(root)

        # uncomment to output decision tree
        # arguments.logger.trace(repr(root))

        return root
