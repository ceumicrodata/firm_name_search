from __future__ import print_function

import difflib
import operator


def ratio(s1, s2):
    m = difflib.SequenceMatcher()
    m.set_seq1(s1)
    m.set_seq2(s2)
    return m.ratio()


def get_closest_match(word, candidates):
    matches = difflib.get_close_matches(word, candidates, 1)
    if matches:
        return matches[0]


def multiword_fuzzy_partial_ratio(s1, s2):
    '''
        Similarity score.

        Calculated of the two strings by looking at common words (or very similar - fuzzy) one sided differences are discarded (-> partial).
    '''
    words1 = s1.split()
    words2 = s2.split()
    ws1 = set(words1)
    ws2 = set(words2)

    # common words
    common = ws1.intersection(ws2)

    # lists of unique words
    unique1 = list(ws1 - common)
    unique2 = list(ws2 - common)

    # fuzzy matches
    cf1 = {w: get_closest_match(w, unique2) for w in unique1}
    cf2 = {w: get_closest_match(w, unique1) for w in unique2}

    # both side agree on fuzzy match
    possible_typos = [(w1, w2) for w1, w2 in cf1.items() if cf2.get(w2) == w1]

    def typos(index):
        return list(map(operator.itemgetter(index - 1), possible_typos))
    typos1 = typos(1)
    typos2 = typos(2)
    sorted_common = sorted(common)
    r1 = ' '.join(sorted_common + typos1) + ' '
    r2 = ' '.join(sorted_common + typos2) + ' '

    # # variants for unique parts:
    # # this one collapses repeated words and sorts the words

    # unique_part1 = ' '.join(sorted(set(unique1) - set(typos1)))
    # unique_part2 = ' '.join(sorted(set(unique2) - set(typos2)))

    # # keeps all unique words in the original order
    unique_part1 = ' '.join(w for w in words1 if w in unique1 and w not in typos1)
    unique_part2 = ' '.join(w for w in words2 if w in unique2 and w not in typos2)

    # # score calculation variants
    # # variant1: scale with a punishment based on the size of the remaining unique bits
    l1 = len(unique_part1)
    l2 = len(unique_part2)
    punish_unique = l1 * l2 / 8.
    score1 = ratio(r1, r2) * (1 - punish_unique / (punish_unique + l1 + l2 + 1))

    # # variant2: extract common and typos, leave unmatched at its place
    score2 = ratio(r1 + unique_part1, r2 + unique_part2)

    # print(score1, score2,, ratio(s1, s2))
    return max(score1, score2)


if __name__ == '__main__':
    def bench(s1, s2):
        print('s1      "%s"' % s1)
        print('s2      "%s"' % s2)
        print('fuzzy  ', multiword_fuzzy_partial_ratio(s1, s2))
        print('difflib', ratio(s1, s2))
        print()

    # they are mostly similar - have close enough words to have "typos"
    bench('hello world beko',     'heko word worl')
    bench('hello world beko srl', 'heko word worl s.r.l.')
    bench('hello world beko srl', 'heko word worl s. r.l.')
    bench('hello world beko srl', 'helko word eko s. r.l.')

    # it should get a small score with either scoring calculation
    bench('hello world beko srl', 'totally different and long and bad and this one is very long and bad and long and bad')

    # these three are interesting as without using the maximum of both scores, at least one of them would go bad with either score calculation
    bench('hello word ag',        'hello world s.r.l.')
    bench('hello world s rl',     'hello world s.r.l.')
    bench('hello world s.r.l.',   'hello world srl and something very long at the end, since extra text is present only in one of the strings it should not matter much in the score')
