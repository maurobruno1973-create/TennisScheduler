"""
Tennis Mixed Doubles Scheduler

Versione 0.2

Motore del programma.
Tutti i dati del torneo vengono letti da config.py
"""

from dataclasses import dataclass
from itertools import combinations

import config


# -------------------------
# Modelli dati
# -------------------------

@dataclass(frozen=True)
class Pair:
    man: str
    woman: str

    @property
    def players(self):
        return {self.man, self.woman}

    def __str__(self):
        return f"{self.man} - {self.woman}"


@dataclass(frozen=True)
class Match:
    pair1: Pair
    pair2: Pair

    @property
    def players(self):
        return self.pair1.players | self.pair2.players

    def is_valid(self):
        return len(self.players) == 4

    def __str__(self):
        return f"{self.pair1}   vs   {self.pair2}"


# -------------------------
# Scheduler
# -------------------------

class TournamentScheduler:

    def __init__(self):

        self.pairs = [
            Pair(man, woman)
            for man, woman in config.PAIRS
        ]

        self.matches = []

    def generate_matches(self):

        self.matches = []

        for p1, p2 in combinations(self.pairs, 2):

            match = Match(p1, p2)

            if match.is_valid():
                self.matches.append(match)

        print(f"Coppie disponibili : {len(self.pairs)}")
        print(f"Partite generate    : {len(self.matches)}")


if __name__ == "__main__":

    scheduler = TournamentScheduler()

    scheduler.generate_matches()
