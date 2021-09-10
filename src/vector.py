"""MisMisQuote module: pattern vectors
"""
import logging as l


class MMQVectors:

    """MisMisQuote Vectors Class

    Vectors with the occurrences of items
    within the search "text"

    Attributes:

        items (Any): Original items list
        vectors (dict): List of occurrences indexed by items
    """

    def __init__(self, items: list):
        """Create a new MMQVectors object

        Creates the vectors from the items

        The searched sequence of items (e.g., a string)
        should be split up into a list of its constituent
        items, (e.g., into characters)

        Args:

            items (list): Items list
        """

        l.debug("MMQVectors init {}".format(items))
        self.items = items
        self.vectors = {}

        if len(items) == 0:
            l.debug("   no items")
            return

        for i in range(0, len(items)):
            item = items[i]
            if item not in self.vectors:
                self.vectors[item] = [False] * len(self.items)
            self.vectors[item][i] = True

    def get_matches(self, item) -> list:
        """Get a list of matches for the item

        The list of matches is the same
        length as the items list and
        is True in the positions where
        the item is present

        Args:
            item (Any): the item to find

        Returns:
            list: list of bools
        """
        if item in self.vectors:
            l.debug(
                "      vector get_matches: {} -> {}".format(item, self.vectors[item]))
            return self.vectors[item]
        else:
            l.debug("      vector get_matches: {} -> none".format(item))
            return [False] * len(self.items)
