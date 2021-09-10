# MisMisQuote

**Find Misspelt|Mispelt|Misspet and Misworded|Rewritten Quotes**

A library to find potenitally misspelt or misworded text from a body of reference texts

## Shift-And Algorithm

MisMisQuote is loosely based on the 'shift-and' algorithm for text matching.

The 'shift-and' algorithm uses a bitmap, i.e., a processor register, to represent how far we have matched the
search string to the reference string.

At each new character, we _shift_ the bitmap towards the more significant bits and put a 1 in
the least significant bit.

Then we _and_ the bitmap with the pre-calculated bitmaps of where that particular character
comes up in the search string.

So, if we have matched 4 characters so far, then, after the _shift_ we will have a 1 bit
in the 5^th^ position. Now if the current character matches, then we should have a 1 bit
in the character's bitmap, too, so the bit would 'survive' the _and_ and continue
to 'bubble up'.

We have a match if we have a 1 in the n^th^ bit, where n is the length of the search string.

## Floats instead of Bits

To be able to score fuzzy matches, we use lists of floats to represent the bitmap, so
at each position we can track not just full matches, but partial matches, too.

When we have some positive number in the n^th^ position, we know that we have found
'something' and the score gives an idea how good the match is.

The threshold can be set to limit the quality of matches to the desired higher or
lower accuracy.
