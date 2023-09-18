import torch

from tree.tree_node import TreeNode


def nodes_are_equal(node1: TreeNode, node2: TreeNode) -> bool:
    if node1.street != node2.street:
        # print(f"Streets are not equal {node1.street} != {node2.street}")
        return False
    if node1.board_string != node2.board_string:
        # print(f"Board strings are not equal {node1.board_string} != {node2.board_string}")
        return False
    if node1.current_player != node2.current_player:
        # print(f"Current players are not equal {node1.current_player} != {node2.current_player}")
        return False
    if not torch.equal(node1.bets, node2.bets):
        # print(f"Bets are not equal {node1.bets} != {node2.bets}")
        return False
    return True


def find_node(node: TreeNode, tree: TreeNode, depth: int):
    if nodes_are_equal(node, tree):
        return tree, depth
    for child in tree.children:
        result, _ = find_node(node, child, depth + 1)
        if result is not None:
            return result, depth
    return None, 0
