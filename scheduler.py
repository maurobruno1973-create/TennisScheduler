"""
Tennis Mixed Doubles Scheduler

Versione 0.2

Motore del programma.
Tutti i dati del torneo vengono letti da config.py
"""

from dataclasses import dataclass
from itertools import combinations

import config

from ortools.sat.python import cp_model

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

        print("\n=== COPPIE DISPONIBILI ===")

        for i, pair in enumerate(self.pairs, start=1):
            print(f"{i:2d}. {pair}")

        print("\nGenerazione partite...")

        for p1, p2 in combinations(self.pairs, 2):

            match = Match(p1, p2)

            if match.is_valid():
                self.matches.append(match)

        print(f"\nPartite valide generate: {len(self.matches)}")

        print("\n=== PRIME 10 PARTITE ===")

        for i, match in enumerate(self.matches[:10], start=1):
            print(f"{i:2d}. {match}")

    def build_model(self):

        print("\nCreazione modello OR-Tools...")

        self.model = cp_model.CpModel()

        self.match_vars = {}

        for i, match in enumerate(self.matches):

            self.match_vars[i] = self.model.NewBoolVar(f"match_{i}")

        print(f"Variabili create: {len(self.match_vars)}")

    def add_basic_constraints(self):

        print("\nAggiunta vincoli base...")

        self.model.Add(
            sum(self.match_vars.values()) == config.NUM_MATCHES
        )

        print(f"Numero partite da selezionare: {config.NUM_MATCHES}")
        
    def solve(self):

        print("\nRisoluzione...")

        solver = cp_model.CpSolver()

        status = solver.Solve(self.model)

        if status != cp_model.OPTIMAL:
            print("Nessuna soluzione.")
            return

        print("Soluzione trovata.\n")

        print("=== PARTITE SELEZIONATE ===")

        count = 1

        for i, match in enumerate(self.matches):

            if solver.Value(self.match_vars[i]):

                print(f"{count:2d}. {match}")

                count += 1

if __name__ == "__main__":

    scheduler = TournamentScheduler()
    scheduler.generate_matches()
    scheduler.build_model()
    scheduler.add_basic_constraints()
    scheduler.solve()
