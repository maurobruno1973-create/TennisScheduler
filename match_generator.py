from itertools import combinations

from models import Match


def generate_matches(pairs):

    matches = []

    for p1, p2 in combinations(pairs, 2):

        match = Match(p1, p2)

        if match.is_valid():
            matches.append(match)

    return matches
