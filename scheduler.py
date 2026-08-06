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

        # OR-Tools
        self.model = None
        self.match_vars = {}

        # Statistiche
        self.player_matches = {}
        self.player_count_vars = {}

        # Target
        self.target_men_matches = 0

        # Ottimizzazione
        self.men_deviation_vars = {}
        self.soft_avoid_vars = []

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

    def build_player_counters(self):

        print("\nCreazione contatori giocatori...")

        self.player_matches = {}

        # inizializza tutti i giocatori
        for man in config.MEN:
            self.player_matches[man] = []

        for woman in config.WOMEN:
            self.player_matches[woman] = []

        # per ogni partita aggiunge la variabile ai 4 giocatori coinvolti
        for i, match in enumerate(self.matches):

            players = (
                match.pair1.man,
                match.pair1.woman,
                match.pair2.man,
                match.pair2.woman,
            )

            for player in players:
                self.player_matches[player].append(self.match_vars[i])

        print("Contatori creati.")

    def build_player_count_variables(self):

        print("\nCreazione variabili conteggio giocatori...")

        self.player_count_vars = {}

        for player, vars_list in self.player_matches.items():

            count = self.model.NewIntVar(
                0,
                len(vars_list),
                f"count_{player}"
            )

            self.model.Add(count == sum(vars_list))

            self.player_count_vars[player] = count

        print(f"Variabili create: {len(self.player_count_vars)}")

    def compute_targets(self):

        total_male_slots = config.NUM_MATCHES * 2

        self.target_men_matches = (
            total_male_slots // len(config.MEN)
        )

        print("\nTarget uomini")
        print("----------------")
        print(f"Partite per uomo: {self.target_men_matches}")

    def build_men_deviation_variables(self):

        print("\nCreazione variabili deviazione uomini...")

        self.men_deviation_vars = {}

        for man in config.MEN:

            deviation = self.model.NewIntVar(
                0,
                config.NUM_MATCHES,
                f"dev_{man}"
            )

            self.model.AddAbsEquality(
                deviation,
                self.player_count_vars[man] - self.target_men_matches
            )

            self.men_deviation_vars[man] = deviation

        print(f"Variabili create: {len(self.men_deviation_vars)}")

    def build_soft_avoid_variables(self):

        print("\nCreazione penalità incontri indesiderati...")

        self.soft_avoid_vars = []

        for i, match in enumerate(self.matches):

            penalty = False

            for p1, p2 in config.SOFT_AVOID_OPPONENTS:

                pair1 = (match.pair1.man, match.pair1.woman)
                pair2 = (match.pair2.man, match.pair2.woman)

                # p1 è nella prima coppia e p2 nella seconda
                cond1 = (p1 in pair1) and (p2 in pair2)

                # oppure viceversa
                cond2 = (p2 in pair1) and (p1 in pair2)

                if cond1 or cond2:
                    penalty = True
                    break

            if penalty:
                self.soft_avoid_vars.append(self.match_vars[i])

        print(f"Partite penalizzate: {len(self.soft_avoid_vars)}")

        if self.soft_avoid_vars:

            print("\nElenco:")

            for i, match in enumerate(self.matches):

                pair1 = (match.pair1.man, match.pair1.woman)
                pair2 = (match.pair2.man, match.pair2.woman)

                for p1, p2 in config.SOFT_AVOID_OPPONENTS:

                    cond1 = (p1 in pair1) and (p2 in pair2)
                    cond2 = (p2 in pair1) and (p1 in pair2)

                    if cond1 or cond2:
                        print(f" - {match}")
                        
    def add_objective(self):

      print("\nFunzione obiettivo")

      objective = 0

      # ----------------------------------
      # Bilanciamento uomini
      # ----------------------------------

      objective += (
        config.OBJECTIVE_WEIGHTS["MEN_BALANCE"]
        * sum(self.men_deviation_vars.values())
      )

      # ----------------------------------
      # Incontri da evitare
      # ----------------------------------

      objective += (
        config.OBJECTIVE_WEIGHTS["SOFT_AVOID_OPPONENTS"]
        * sum(self.soft_avoid_vars)
      )

      self.model.Minimize(objective)

      print("Funzione obiettivo impostata.")


    def add_women_constraints(self):

        print("\nVincolo: tutte le donne giocano lo stesso numero di partite...")

        women = config.WOMEN

        for i in range(len(women) - 1):
            self.model.Add(
                self.player_count_vars[women[i]]
                ==
                self.player_count_vars[women[i + 1]]
            )

        print("Vincolo aggiunto.")


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

        print("\n=== PARTITE PER GIOCATORE ===")

        for player in sorted(self.player_count_vars):

            print(
                f"{player:10} "
                f"{solver.Value(self.player_count_vars[player])}"
            )

            
        print("\n=== DEVIAZIONE UOMINI ===")

        total = 0

        for man in config.MEN:

            dev = solver.Value(self.men_deviation_vars[man])

            print(f"{man:10} {dev}")

            total += dev

        print("----------------------")
        print(f"Totale      {total}")




if __name__ == "__main__":

    scheduler = TournamentScheduler()

    scheduler.generate_matches()
    scheduler.build_model()
    scheduler.build_player_counters()
    scheduler.build_player_count_variables()
    scheduler.compute_targets()

    scheduler.build_men_deviation_variables()
    scheduler.build_soft_avoid_variables()
    scheduler.add_basic_constraints()
    scheduler.add_women_constraints()
    scheduler.add_objective()
    
    scheduler.solve()
