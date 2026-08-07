"""
Tennis Mixed Doubles Scheduler

Versione 0.5

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
        self.opponent_played_vars = {}

        # Target
        self.target_men_matches = 0

        # Ottimizzazione
        self.men_deviation_vars = {}
        self.soft_avoid_vars = []

        # Statistiche future
        self.opponent_count_vars = {}


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

        # ----------------------------------
        # Verifica partite duplicate
        # ----------------------------------

        unique_matches = set()

        for match in self.matches:

            pair1 = str(match.pair1)
            pair2 = str(match.pair2)

            key = tuple(sorted((pair1, pair2)))

            unique_matches.add(key)

        duplicates = len(self.matches) - len(unique_matches)

        print(f"Partite uniche: {len(unique_matches)}")
        print(f"Partite duplicate: {duplicates}")


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
    
    def build_opponent_count_variables(self):

      print("\nCreazione variabili Opponent Matrix...")

      self.opponent_count_vars = {}

      players = sorted(self.player_count_vars.keys())

      count = 0

      for i in range(len(players)):
          for j in range(i + 1, len(players)):

              p1 = players[i]
              p2 = players[j]

              self.opponent_count_vars[(p1, p2)] = (
                  self.model.NewIntVar(
                      0,
                      config.NUM_MATCHES,
                      f"opp_{p1}_{p2}"
                  )
              )

              count += 1

      print(f"Variabili create: {count}")

    def build_opponent_played_variables(self):

      print("\nCreazione variabili Opponent Played...")

      self.opponent_played_vars = {}

      for players in self.opponent_count_vars:

        p1, p2 = players

        self.opponent_played_vars[players] = (
            self.model.NewBoolVar(
                f"played_{p1}_{p2}"
            )
        )

      print(
        f"Variabili create: {len(self.opponent_played_vars)}"
      )


    def add_opponent_count_constraints(self):

      print("\nCollegamento Opponent Matrix...")

      for (p1, p2), count_var in self.opponent_count_vars.items():

        opponent_matches = []

        for match_index, match in enumerate(self.matches):

            team1 = [match.pair1.man, match.pair1.woman]
            team2 = [match.pair2.man, match.pair2.woman]

            opponents = (
                (p1 in team1 and p2 in team2)
                or
                (p1 in team2 and p2 in team1)
            )

            if opponents:
                opponent_matches.append(
                    self.match_vars[match_index]
                )

        self.model.Add(
            count_var == sum(opponent_matches)
        )
      
      print(f"Vincoli creati: {len(self.opponent_count_vars)}")


    def add_opponent_played_constraints(self):

      print("\nCollegamento variabili Opponent Played...")

      for key in self.opponent_played_vars:

          count_var = self.opponent_count_vars[key]
          played_var = self.opponent_played_vars[key]

          # Se played = 0 allora count = 0
          self.model.Add(count_var == 0).OnlyEnforceIf(
              played_var.Not()
          )

          # Se played = 1 allora count >= 1
          self.model.Add(count_var >= 1).OnlyEnforceIf(
              played_var
          )

      print(
          f"Vincoli creati: {len(self.opponent_played_vars)}"
      )

   
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

      # ----------------------------------
      # Massimizzare avversari diversi
      # ----------------------------------
      # opponent_played_vars vale:
      #   1 = i due giocatori si sono affrontati
      #   0 = non si sono mai affrontati
      #
      # Poiché il modello MINIMIZZA, sottraiamo
      # il numero di avversari diversi.

      objective -= (
          config.OBJECTIVE_WEIGHTS["DIFFERENT_OPPONENTS"]
          * sum(self.opponent_played_vars.values())
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

        print("=== CONTRIBUTO FUNZIONE OBIETTIVO ===")

        men_balance = (
            config.OBJECTIVE_WEIGHTS["MEN_BALANCE"]
            * sum(
                  solver.Value(var)
                  for var in self.men_deviation_vars.values()
            )
        )

        soft_avoid = (
            config.OBJECTIVE_WEIGHTS["SOFT_AVOID_OPPONENTS"]
            * sum(
                  solver.Value(var)
                  for var in self.soft_avoid_vars
            )
        )

        different_opponents = (
            config.OBJECTIVE_WEIGHTS["DIFFERENT_OPPONENTS"]
            * sum(
                  solver.Value(var)
                  for var in self.opponent_played_vars.values()
            )
        )

        print(
            f"Bilanciamento uomini:       {men_balance}"
        )

        print(
            f"Incontri da evitare:        {soft_avoid}"
        )

        print(
            f"Avversari diversi:         -{different_opponents}"
        )

        print("-------------------------------")

        print(
            f"Totale obiettivo:           "
            f"{men_balance + soft_avoid - different_opponents}"
        )




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


        print("\n=== AVVERSARI DIVERSI ===")

        for player in sorted(self.player_count_vars):

            opponents = set()

            for (p1, p2), played_var in self.opponent_played_vars.items():

                if solver.Value(played_var):

                    if player == p1:
                       opponents.add(p2)

                    elif player == p2:
                       opponents.add(p1)

            print(
                f"{player:10} "
                f"{len(opponents)} -> "
                f"{', '.join(sorted(opponents))}"
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
    scheduler.build_opponent_count_variables()
    scheduler.build_opponent_played_variables()

    scheduler.add_opponent_count_constraints()
    scheduler.add_opponent_played_constraints()
    scheduler.add_basic_constraints()
    scheduler.add_women_constraints()
    scheduler.add_objective()
    
    scheduler.solve()
