"""MisMisQuote module: match tracking
"""

import logging as l

from utils import _or


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

    def match(self, matches: list) -> float:
        """Update the tracker with the latest matches

        The matches list must be a list of bools and
        the less than or the same length as set in init

        Args:

            matches (list): list of matches

        Raises:

            ValueError: matches list is not the same length

        Returns:

            float: level of last match, null if too early
        """
        if len(matches) != self.length:
            raise ValueError("matches list has length %d different than set before %d" % (
                len(matches), self.length
            ))

        newtracker = self._and_tracker(
            # shift the last tracker
            self._shift_last_tracker(),
            # 'and' with the matches
            matches
        )

        self.tracker.append(newtracker)

        l.debug("      tracker match {}: {}".format(matches, newtracker))

        score = newtracker[0]

        if self.allowed_differences:
            # we will 'or' with later 'bits'
            for j in range(0, self.allowed_differences):
                score = _or(score, newtracker[j+1], j)
                if j < len(self.tracker)-1:
                    alttracker = self._and_tracker(
                        # shift the historic tracker
                        self._shift_old_tracker(j),
                        # 'and' with the matches
                        matches
                    )
                    score = _or(score, alttracker[0], j)
                    l.debug("      alt tracker {} {}: {}".format(
                        j, matches, alttracker))

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
            if not matches[self.length - i - 1]:
                # if not a match, set it to zero or reduce it by the multiplier
                newtracker[i] *= self.nomatch_multiplier

        return newtracker
