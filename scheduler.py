"""
Tennis Mixed Doubles Scheduler

Versione 0.13

Motore del programma.
Tutti i dati del torneo vengono letti da config.py
"""


import config

from models import Pair, Match

from match_generator import generate_matches
from validator import validate_solution
from reporter import report_solution
from reporter import report_solution

from ortools.sat.python import cp_model



# --------------------------------------
# Modelli dati rimossi aggiunti in model
# --------------------------------------


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

        self.matches = generate_matches(self.pairs)

        print("\n=== COPPIE DISPONIBILI ===")

        for i, pair in enumerate(self.pairs, start=1):
            print(f"{i:2d}. {pair}")

        print("\nGenerazione partite...")

        print(
            f"\nPartite valide generate: "
            f"{len(self.matches)}"
        )

        # ----------------------------------
        # Verifica partite duplicate
        # ----------------------------------

        unique_matches = set()

        for match in self.matches:

            pair1 = str(match.pair1)
            pair2 = str(match.pair2)

            key = tuple(sorted((pair1, pair2)))

            unique_matches.add(key)

        duplicates = (
            len(self.matches)
            - len(unique_matches)
        )

        print(f"Partite uniche: {len(unique_matches)}")
        print(f"Partite duplicate: {duplicates}")


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

    def check_pair_distribution(self):

        num_pairs = len(self.pairs)
        num_matches = config.NUM_MATCHES

        total_pair_slots = num_matches * 2

        print("\n=== CONTROLLO CONFIGURAZIONE COPPIE ===")
        print(f"Coppie disponibili:        {num_pairs}")
        print(f"Partite richieste:         {num_matches}")
        print(f"Partecipazioni coppie:     {total_pair_slots}")

        # ----------------------------------
        # Verifica distribuzione uniforme
        # ----------------------------------

        if total_pair_slots % num_pairs == 0:

            matches_per_pair = (
                total_pair_slots // num_pairs
            )

            print(
                f"Partite per coppia:        "
                f"{matches_per_pair}"
            )

            print("Configurazione valida:     OK")

        else:

            print(
                "Configurazione valida:     ERRORE"
            )

            print(
                "Non è possibile assegnare "
                "lo stesso numero di partite "
                "a tutte le coppie."
            )

        # ----------------------------------
        # Distribuzioni possibili
        # ----------------------------------

        print("\nDistribuzioni possibili:")

        max_matches_per_pair = 6

        for matches_per_pair in range(
            1,
            max_matches_per_pair + 1
        ):

            required_matches = (
                num_pairs * matches_per_pair
            ) // 2

            print(
                f"{matches_per_pair} partita/e per coppia"
                f" -> {required_matches} partite"
            )



    def compute_targets(self):

        # ----------------------------------
        # Target uomini
        # ----------------------------------

        total_male_slots = config.NUM_MATCHES * 2

        self.target_men_matches = (
            total_male_slots // len(config.MEN)
        )

        # ----------------------------------
        # Target donne
        # ----------------------------------

        total_woman_slots = config.NUM_MATCHES * 2

        self.target_women_matches = (
            total_woman_slots // len(config.WOMEN)
        )

        # ----------------------------------
        # Target coppie
        # ----------------------------------

        total_pair_slots = config.NUM_MATCHES * 2

        if total_pair_slots % len(self.pairs) != 0:
            raise ValueError(
                "Il numero di partite non permette "
                "una distribuzione uguale tra tutte le coppie."
            )

        self.target_pair_matches = (
            total_pair_slots // len(self.pairs)
        )

        print("\nTarget giocatori")
        print("----------------")
        print(
              f"Partite per uomo:   {self.target_men_matches}"
        )
        print(
              f"Partite per donna:  {self.target_women_matches}"
        )
        print(
              f"Partite per coppia: {self.target_pair_matches}"
        )

    def build_women_deviation_variables(self):

        print("\nCreazione variabili deviazione donne...")

        self.women_deviation_vars = {}

        for woman in config.WOMEN:

            deviation = self.model.NewIntVar(
                0,
                config.NUM_MATCHES,
                f"dev_{woman}"
            )

            self.model.AddAbsEquality(
                deviation,
                self.player_count_vars[woman] - self.target_women_matches
            )

            self.women_deviation_vars[woman] = deviation

        print(
            f"Variabili create: "
            f"{len(self.women_deviation_vars)}"
        )

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
      # Bilanciamento donne
      # ----------------------------------

      objective += (
          config.OBJECTIVE_WEIGHTS["WOMEN_BALANCE"]
          * sum(self.women_deviation_vars.values())
      )
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

        print("\nBilanciamento partite donne...")

          # Il numero di partite delle donne NON è un vincolo rigido.
          # Il bilanciamento viene gestito dalla funzione obiettivo.

        print("Bilanciamento donne impostato come obiettivo soft.")

    def add_basic_constraints(self):

        print("\nAggiunta vincoli base...")

        self.model.Add(
            sum(self.match_vars.values()) == config.NUM_MATCHES
        )

        print(f"Numero partite da selezionare: {config.NUM_MATCHES}")


        # ----------------------------------
        # Vincolo partite per coppia
        # ----------------------------------

        if config.ENFORCE_EQUAL_PAIR_MATCHES:

            for pair in self.pairs:

                pair_match_count = sum(
                    self.match_vars[i]
                    for i, match in enumerate(self.matches)
                    if match.pair1 == pair or match.pair2 == pair
                )

                self.model.Add(
                    pair_match_count == self.target_pair_matches
                )

            print(
                "Vincolo: tutte le coppie giocano "
                "lo stesso numero di partite..."
            )

    def solve(self):

        print("\nRisoluzione...")

        solver = cp_model.CpSolver()

        status = solver.Solve(self.model)

        if status != cp_model.OPTIMAL:

            print("Nessuna soluzione.")

            return

        print("Soluzione trovata.\n")

        report_solution(self, solver)

        validate_solution(self, solver)

        return solver

