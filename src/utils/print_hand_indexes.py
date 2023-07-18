import game.card_tools as card_tools
import settings.game_settings as game_settings
import numpy as np


def main():
    hands = []
    cards = []
    for rank in game_settings.rank_table:
        for suit in game_settings.suit_table:
            cards.append(rank + suit)
    index_hands = []
    for card_one_index in range(len(cards)):
        for card_two_index in range(card_one_index + 1, len(cards)):
            index_hands.append([card_one_index, card_two_index])
            hands.append(cards[card_one_index] + cards[card_two_index])
    indexes = [card_tools.string_to_hole_index(hand) for hand in hands]
    sort_index = np.argsort(indexes)
    hands = np.array(hands)
    hands = hands[sort_index]
    for hand in hands:
        print(f"\"{hand}\", ", end="")


if __name__ == '__main__':
    main()
