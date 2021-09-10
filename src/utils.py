"""MisMisQuote module: utility functions
"""


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
