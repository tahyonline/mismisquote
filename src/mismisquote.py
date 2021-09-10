import logging as l


def _or(newscore: float, oldscore: float, howold: int) -> float:
    """Logical 'or', but with float scores

    An internal utility function to weight old scores
    and 'or' them, i.e., add them to new scores
    to calculate the matches if there are misses

    Adds the two scores, but limits the return value
    to 1.0

    The howold value weights down the old score like:

    - 0: divide by 2
    - 1: divide by 3
    - 2: divide by 4

    This is so that howold can be the loop index variable

    Args:
        newscore (float): the full match score
        oldscore (float): a previous score
        howold (int): how far back we are going

    Returns:
        float: the 'or'-ed score
    """
    if newscore < 0.0 or newscore > 1.0:
        ValueError("newscore %f must be >= 0.0 and <= 1.0" % newscore)
    if oldscore < 0.0 or oldscore > 1.0:
        ValueError("oldscore %f must be >= 0.0 and <= 1.0" % oldscore)
    if howold < 0:
        ValueError("howold %d must be >= 0")

    return min(1.0, newscore + oldscore/(2+howold))


class MisMisQuote:
    def __init__(self, items: list, *, allowed_differences: int = 0, nomatch_multiplier: float = 0.0, threshold: float = 1.0):
        """Create new MisMisQuote object for a sequece or pattern

        This sequence can then be looked for in the reference

        There are two ways to set up fuzzy matching:

        - allowed_differences: number of items missing or different, so that the 
          score will be 1/1 if full match, 1/2 if one miss, 1/3 if two misses etc.
        - nomatch_multiplier: the score will be reduced by multiplying with this
          value between 0.0 and 1.0, so that each miss reduces the total score

        The objective is not to be very accurate about the match score, rather
        to be able to rank the matches

        The threshold must be set to a number between 0.0 and 1.0 to get
        non-exact matches

        Args:

            length (int): length of the pattern
            allowed_differences (int, optional): number of differences allowed. Defaults to 0.
            nomatch_multiplier (float, optional): multiplier if the current pattern item does not match the reference. Defaults to 0.0.
            threshold (float, optional): what match scores should be included in the results. Defaults to 1.0.

        Raises:

            ValueError: length <= 0
            ValueError: allowed_differences < 0
            ValueError: nomatch_multiplier < 0.0 or >= 1.0
            ValueError: threshold < 0.0 or > 1.0
        """
        if items is None or len(items) == 0:
            raise ValueError("items list empty")
        if allowed_differences < 0:
            raise ValueError("allowed_differences %d must be >= 0" %
                             allowed_differences)
        if nomatch_multiplier < 0.0 or nomatch_multiplier >= 1.0:
            raise ValueError(
                "nomatch_multiplier %f must be >= 0 and < 1.0" % nomatch_multiplier)
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(
                "threshold %f must be >= 0 and <= 1.0" % threshold)

        self.items = items
        self.threshold = threshold

        self.allowed_differences = allowed_differences
        self.nomatch_multiplier = nomatch_multiplier

        self.vectors = MMQVectors(
            self.items,
            allowed_differences=self.allowed_differences,
            nomatch_multiplier=self.nomatch_multiplier,
            threshold=self.threshold
        )

    def find_in(self, reference_items: list) -> list:
        """Find the search sequence in the reference provided

        Return a list of full and potential matches,
        if any

        Matching fuzziness is based on the parameters
        set at init

        The results are returned in a list of tuples with
        each tuple including the zero-based location of the
        end of the match and the score

        If the threshold value was set to lower than 1.0 at init,
        then incomplete matches will be included

        Args:
            reference_items (list): the reference sequence as a list of items

        Returns:
            list: a list of tuples with location and score for each match
        """
        tracker = MMQTracker(
            len(self.items),
            allowed_differences=self.allowed_differences,
            nomatch_multiplier=self.nomatch_multiplier,
            threshold=self.threshold
        )

        results = []

        for i in range(0, len(reference_items)):
            score = tracker.shiftand(
                self.vectors.get_locmap(reference_items[i])
            )
            results.append((i, score))
            if score >= self.threshold:
                l.debug("   matched at %d (%f)" % (i, score))

        results.sort(key=lambda res: res[1], reverse=True)

        return list(filter(lambda res: res[1] >= self.threshold, results))


class MMQVectors:

    """MisMisQuote Vectors Class

    Vectors with the occurrences of items
    within the search "text"

    Attributes:

        items (Any): Original items list
        vectors (dict): List of occurrences indexed by items
    """

    def __init__(self, items: list, *, allowed_differences: int = 0, nomatch_multiplier: float = 0.0, threshold: float = 1.0):
        """Create a new MMQVectors object

        Creates the vectors from the items

        The searched sequence of items (e.g., a string)
        should be split up into a list of its constituent
        items, (e.g., into characters)

        Args:

            items (list): Items list
            allowed_differences (int, optional): number of differences allowed. Defaults to 0.
            nomatch_multiplier (float, optional): multiplier if the current pattern item does not match the reference. Defaults to 0.0.
            threshold (float, optional): what match scores should be included in the results. Defaults to 1.0.

        Raises:

            ValueError: allowed_differences < 0
            ValueError: nomatch_multiplier < 0.0 or >= 1.0
            ValueError: threshold < 0.0 or > 1.0
        """

        l.debug("MMQVectors init {}".format(items))
        if allowed_differences < 0:
            raise ValueError("allowed_differences %d must be >= 0" %
                             allowed_differences)
        if nomatch_multiplier < 0.0 or nomatch_multiplier >= 1.0:
            raise ValueError(
                "nomatch_multiplier %f must be >= 0 and < 1.0" % nomatch_multiplier)
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(
                "threshold %f must be >= 0 and <= 1.0" % threshold)

        self.items = items
        self.vectors = {}

        self.threshold = threshold
        self.allowed_differences = allowed_differences
        self.nomatch_multiplier = nomatch_multiplier

        if len(items) == 0:
            l.debug("   no items")
            return

        for i in range(0, len(items)):
            item = items[i]
            if item not in self.vectors:
                self.vectors[item] = {
                    'locmap': [0.0] * len(self.items),
                    'mmq': None
                }
                if isinstance(item, str) and len(item) > 1:
                    self.vectors[item]['mmq'] = MisMisQuote(
                        list(item),
                        allowed_differences=self.allowed_differences,
                        nomatch_multiplier=self.nomatch_multiplier,
                        threshold=self.threshold
                    )
            self.vectors[item]['locmap'][i] = 1.0

    def get_locmap(self, item) -> list:
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
                "      vector get_matches: {} -> {}".format(item, self.vectors[item]['locmap']))
            return self.vectors[item]['locmap']
        else:
            potentials = []

            for k in self.vectors:
                if 'mmq' in self.vectors[k] and self.vectors[k]['mmq'] is not None:
                    _mmq = self.vectors[k]['mmq']
                    res = _mmq.find_in(list(item))
                    if res:
                        potentials.append((k, res[0][1]))

            if len(potentials):
                potentials.sort(key=lambda r: r[1], reverse=True)
                return list(
                    map(
                        lambda x: x * potentials[0][1],
                        self.vectors[potentials[0][0]]['locmap']
                    )
                )

            else:
                l.debug("      vector get_matches: {} -> none".format(item))
                return [0.0] * len(self.items)


class MMQTracker:
    def __init__(self, length: int, *, allowed_differences: int = 0, nomatch_multiplier: float = 0.0, threshold: float = 1.0):
        """Create new MMQTracker object

        Args:

            length (int): length of the pattern
            allowed_differences (int, optional): number of differences allowed. Defaults to 0.
            nomatch_multiplier (float, optional): multiplier if the current pattern item does not match the reference. Defaults to 0.0.
            threshold (float, optional): what match scores should be included in the results. Defaults to 1.0.

        Raises:

            ValueError: length <= 0
            ValueError: allowed_differences < 0
            ValueError: nomatch_multiplier < 0.0 or >= 1.0
            ValueError: threshold < 0.0 or > 1.0
        """

        if length <= 0:
            raise ValueError("length %d must be > 0" % length)
        if allowed_differences < 0:
            raise ValueError("allowed_differences %d must be >= 0" %
                             allowed_differences)
        if allowed_differences >= length:
            raise ValueError("allowed_differences %d must be < length %d" %
                             (allowed_differences, length))
        if nomatch_multiplier < 0.0 or nomatch_multiplier >= 1.0:
            raise ValueError(
                "nomatch_multiplier %f must be >= 0 and < 1.0" % nomatch_multiplier)
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(
                "threshold %f must be >= 0 and <= 1.0" % threshold)

        self.length = length
        self.allowed_differences = allowed_differences
        self.nomatch_multiplier = nomatch_multiplier
        self.threshold = threshold

        self.tracker = []

    def shiftand(self, locmap: list) -> float:
        """Update the tracker with the locmap

        The locmap list must be a list of bools and
        the less than or the same length as set in init

        Presumably, the locmap will come from the
        MMQVectors object that has the location maps
        for each item

        Args:

            locmap (list): list of locmap

        Raises:

            ValueError: locmap list is not the same length

        Returns:

            float: level of last match, null if too early
        """
        if len(locmap) != self.length:
            raise ValueError("locmap list has length %d different than set before %d" % (
                len(locmap), self.length
            ))

        newtracker = self._and_tracker(
            # shift the last tracker
            self._shift_last_tracker(),
            # 'and' with the locmap
            locmap
        )

        self.tracker.append(newtracker)

        l.debug("      tracker match {}: {}".format(locmap, newtracker))

        score = newtracker[0]

        if self.allowed_differences:
            # we will 'or' with later 'bits'
            for j in range(0, self.allowed_differences):
                score = _or(score, newtracker[j+1], j)
                if j < len(self.tracker)-1:
                    alttracker = self._and_tracker(
                        # shift the historic tracker
                        self._shift_old_tracker(j),
                        # 'and' with the locmap
                        locmap
                    )
                    score = _or(score, alttracker[0], j)
                    l.debug("      alt tracker {} {}: {}".format(
                        j, locmap, alttracker))

        return score

    def _shift_last_tracker(self) -> list:
        if len(self.tracker):
            # have trackers already
            return self.tracker[-1][1:] + [1.0]
        else:
            # no trackers, yet, new empty tracker
            filler = 0.0
            if self.nomatch_multiplier > 0.0:
                filler = self.nomatch_multiplier
            elif self.allowed_differences > 0:
                filler = 1.0 / (self.allowed_differences + 1)
            return [filler] * (self.length - 1) + [1.0]

    def _shift_old_tracker(self, j) -> list:
        return self.tracker[-(j+2)][j+2:] + [1.0] * (j+2)

    def _and_tracker(self, newtracker: list, matches: list) -> list:
        for i in range(0, self.length):
            # go through the new tracker and 'and' it with the matches
            if matches[self.length - i - 1] == 0.0:
                # if not a match, set it to zero or reduce it by the multiplier
                newtracker[i] *= self.nomatch_multiplier
            elif matches[self.length - i - 1] < 1.0:
                newtracker[i] *= matches[self.length - i - 1]

        return newtracker


if __name__ == '__main__':
    import sys
    import re
    logger = l.getLogger()
    logger.setLevel(l.INFO)
    handler = l.StreamHandler(sys.stdout)
    handler.setLevel(l.INFO)
    formatter = l.Formatter('%(levelname)7s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    l.info("MisMisQuote Testing")

    to_find = "Lorem ipsum! Dolor."
    find_in = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Pellentesque eu tincidunt tortor aliquam nulla. Justo nec ultrices dui sapien eget mi proin sed. Dictum at tempor commodo ullamcorper a lacus vestibulum sed arcu. Tempor orci dapibus ultrices in iaculis nunc. Nunc id cursus metus aliquam eleifend mi in. Condimentum id venenatis a condimentum. Cras semper auctor neque vitae. Faucibus nisl tincidunt eget nullam non nisi est. Mi eget mauris pharetra et ultrices neque ornare aenean. Bibendum ut tristique et egestas quis ipsum suspendisse ultrices.

Lorem ipsum dolor sit amet. Diam quis enim lobortis scelerisque fermentum dui faucibus in. Nec ullamcorper sit amet risus. Tristique et egestas quis ipsum. Magna fringilla urna porttitor rhoncus dolor. Arcu cursus vitae congue mauris rhoncus aenean vel. Velit ut tortor pretium viverra suspendisse potenti. Fringilla urna porttitor rhoncus dolor purus non enim praesent. Commodo elit at imperdiet dui. Sollicitudin tempor id eu nisl nunc. Purus ut faucibus pulvinar elementum integer enim neque volutpat. Habitant morbi tristique senectus et netus et malesuada fames. Orci a scelerisque purus semper eget duis at tellus at. Neque convallis a cras semper. Metus aliquam eleifend mi in nulla. Quisque non tellus orci ac auctor augue.

Egestas fringilla phasellus faucibus scelerisque eleifend. Justo eget magna fermentum iaculis eu non diam. Fusce id velit ut tortor pretium viverra suspendisse. Donec ultrices tincidunt arcu non sodales. Est velit egestas dui id ornare arcu odio ut sem. In mollis nunc sed id. Risus nullam eget felis eget nunc lobortis mattis aliquam. Eget magna fermentum iaculis eu. Elit ullamcorper dignissim cras tincidunt lobortis feugiat vivamus at augue. In dictum non consectetur a erat nam at lectus urna. At tempor commodo ullamcorper a lacus. Id leo in vitae turpis massa sed elementum tempus. Sapien pellentesque habitant morbi tristique senectus et netus et malesuada. Urna neque viverra justo nec. Velit laoreet id donec ultrices.

Enim ut sem viverra aliquet eget sit. Non curabitur gravida arcu ac tortor dignissim convallis aenean et. Blandit turpis cursus in hac habitasse platea dictumst quisque sagittis. Eget felis eget nunc lobortis mattis aliquam faucibus. Condimentum id venenatis a condimentum. Montes nascetur ridiculus mus mauris vitae ultricies leo integer malesuada. Dignissim enim sit amet venenatis urna. Turpis massa sed elementum tempus egestas sed sed. Sit amet volutpat consequat mauris nunc congue nisi vitae. Nunc aliquet bibendum enim facilisis gravida. Auctor urna nunc id cursus metus aliquam eleifend mi. Morbi tincidunt augue interdum velit euismod in pellentesque.

Id aliquet lectus proin nibh nisl. Aenean sed adipiscing diam donec adipiscing tristique risus nec. Quam quisque id diam vel quam elementum pulvinar etiam. Faucibus vitae aliquet nec ullamcorper sit amet risus. Non quam lacus suspendisse faucibus. Vestibulum lorem sed risus ultricies tristique nulla aliquet enim tortor. Eu tincidunt tortor aliquam nulla facilisi. Molestie nunc non blandit massa enim nec dui nunc. Tincidunt nunc pulvinar sapien et. Lectus urna duis convallis convallis tellus id interdum velit.
    """
    find_in_short = "ipsum dolor!"

    to_find_items = list(filter(None, re.split(r'\W+', to_find.lower())))
    reference_items = list(filter(None, re.split(r'\W+', find_in.lower())))
    short_reference_items = list(
        filter(None, re.split(r'\W+', find_in_short.lower())))

    l.info("**********************************\nTest case 1: full matching in long reference")
    lorem = MisMisQuote(to_find_items)
    results = lorem.find_in(reference_items)
    l.info("Results: {}".format(results))

    l.info("**********************************\nTest case 2: fuzzy match multiplier 0.5, long reference")
    lorem = MisMisQuote(to_find_items, nomatch_multiplier=0.5, threshold=0.5)
    results = lorem.find_in(reference_items)
    l.info("Results: {}".format(results))

    l.info("**********************************\nTest case 3: fuzzy match multiplier 0.5, short reference")
    lorem = MisMisQuote(to_find_items, nomatch_multiplier=0.5, threshold=0.5)
    results = lorem.find_in(short_reference_items)
    l.info("Results: {}".format(results))

    l.info("**********************************\nTest case 4: fuzzy match 1 allowed difference, long reference")
    lorem = MisMisQuote(to_find_items, allowed_differences=1, threshold=0.5)
    results = lorem.find_in(reference_items)
    l.info("Results: {}".format(results))

    l.info("**********************************\nTest case 5: fuzzy match 1 allowed difference, short reference")
    lorem = MisMisQuote(to_find_items, allowed_differences=1, threshold=0.5)
    results = lorem.find_in(short_reference_items)
    l.info("Results: {}".format(results))
