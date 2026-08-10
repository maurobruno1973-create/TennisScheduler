"""
Tennis Mixed Doubles Scheduler

Versione 0.15

Motore del programma.
Tutti i dati del torneo vengono letti da config.py
"""


import config

from models import Pair, Match

from match_generator import generate_matches
from validator import validate_solution
from reporter import report_solution
from reporter import report_solution, report_final_solution

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

        #print("\n=== COPPIE DISPONIBILI ===")

        #for i, pair in enumerate(self.pairs, start=1):
        #    print(f"{i:2d}. {pair}")

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

        #print("\nCreazione contatori giocatori...")

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

        #print("Contatori creati.")

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

        #print("\nCreazione variabili deviazione donne...")

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

        #print(
        #    f"Variabili create: "
        #    f"{len(self.women_deviation_vars)}"
        #)

    def build_men_deviation_variables(self):

        #print("\nCreazione variabili deviazione uomini...")

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

        #print(f"Variabili create: {len(self.men_deviation_vars)}")

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

        #if self.soft_avoid_vars:

            #print("\nElenco:")

            #for i, match in enumerate(self.matches):

            #    pair1 = (match.pair1.man, match.pair1.woman)
            #    pair2 = (match.pair2.man, match.pair2.woman)

            #    for p1, p2 in config.SOFT_AVOID_OPPONENTS:

            #        cond1 = (p1 in pair1) and (p2 in pair2)
            #        cond2 = (p2 in pair1) and (p1 in pair2)

            #        if cond1 or cond2:
            #            print(f" - {match}")
    
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

      #print("\nCollegamento Opponent Matrix...")

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
      
      #print(f"Vincoli creati: {len(self.opponent_count_vars)}")


    def add_opponent_played_constraints(self):

      #print("\nCollegamento variabili Opponent Played...")

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

      #print(
      #    f"Vincoli creati: {len(self.opponent_played_vars)}"
      #)

   
    def add_objective(self):

      #print("\nFunzione obiettivo")

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

      #print("Funzione obiettivo impostata.")

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

    def enumerate_optimal_solutions(
        self,
        optimal_objective,
        max_solutions=100
    ):

        print("\n==========================================")
        print("ENUMERAZIONE SOLUZIONI OTTIMALI")
        print("==========================================")

        print(f"Obiettivo ottimale: {optimal_objective}")
        print(f"Limite temporaneo: {max_solutions}")

        # ==================================================
        # 1. COPIA DEL MODELLO
        # ==================================================

        model = self.model.clone()

        # Ricostruiamo l'espressione dell'obiettivo
        objective = 0

        objective += (
            config.OBJECTIVE_WEIGHTS["WOMEN_BALANCE"]
            * sum(self.women_deviation_vars.values())
        )

        objective += (
            config.OBJECTIVE_WEIGHTS["MEN_BALANCE"]
            * sum(self.men_deviation_vars.values())
        )

        objective += (
            config.OBJECTIVE_WEIGHTS["SOFT_AVOID_OPPONENTS"]
            * sum(self.soft_avoid_vars)
        )

        objective -= (
            config.OBJECTIVE_WEIGHTS["DIFFERENT_OPPONENTS"]
            * sum(self.opponent_played_vars.values())
        )

        # ==================================================
        # 2. RIMUOVIAMO L'OBIETTIVO
        # ==================================================

        model.clear_objective()

        # Manteniamo solo le soluzioni che hanno
        # esattamente lo stesso valore ottimale.
        model.add(
            objective == int(optimal_objective)
        )

        # ==================================================
        # 3. CALLBACK
        # ==================================================

        class SolutionCounter(
            cp_model.CpSolverSolutionCallback
        ):

            # 3.1 INIT

            def __init__(
                self,
                scheduler,
                model,
                max_solutions
            ):

                super().__init__()

                self.scheduler = scheduler
                self.model = model
                self.max_solutions = max_solutions

                # ------------------------------------------
                # Contatori generali
                # ------------------------------------------

                self.count = 0
                self.solutions_data = []
                self.best_dd_solutions_data = []

                # ------------------------------------------
                # Risultati diagnostici
                # ------------------------------------------

                self.women_matrix_patterns = {}
                self.men_matrix_patterns = {}
                self.ud_matrix_patterns = {}

                self.uniformity_uu = {}
                self.uniformity_ud = {}
                self.new_uniformity_dd = {}

                self.uu_ud_combinations = {}

                self.best_dd_penalty = None
                self.best_dd_solutions = 0

                self.best_men_penalty = None

                # ------------------------------------------
                # Ricostruiamo le match_vars nella COPIA
                # del modello
                # ------------------------------------------

                self.match_vars = {}

                for i, var in scheduler.match_vars.items():

                    self.match_vars[i] = (
                        model.get_bool_var_from_proto_index(
                            var.index
                        )
                    )

            # ==================================================
            # 3.2 - CALLBACK DI OGNI SOLUZIONE
            # ==================================================

            def on_solution_callback(self):

                self.count += 1

                # ==========================================
                # 3.2.1. PARTITE SELEZIONATE
                # ==========================================

                selected_matches = []

                for i, var in self.match_vars.items():

                    if self.Value(var):

                        selected_matches.append(
                            self.scheduler.matches[i]
                        )

                # ==========================================
                # 3.2.2 DONNA × DONNA
                # ==========================================

                women_opponent_counts = {}

                for match in selected_matches:

                    w1 = match.pair1.woman
                    w2 = match.pair2.woman

                    pair = tuple(
                        sorted((w1, w2))
                    )

                    women_opponent_counts[pair] = (
                        women_opponent_counts.get(pair, 0)
                        + 1
                    )

                # ------------------------------------------
                # 3.2.2 Aggiungiamo anche le coppie mai incontrate
                # ------------------------------------------

                for i, w1 in enumerate(config.WOMEN):

                    for w2 in config.WOMEN[i + 1:]:

                        pair = tuple(
                            sorted((w1, w2))
                        )

                        if pair not in women_opponent_counts:

                            women_opponent_counts[pair] = 0

                # ------------------------------------------
                # 3.2.2 Struttura D×D
                # ------------------------------------------

                women_distribution = {}

                for count in (
                    women_opponent_counts.values()
                ):

                    women_distribution[count] = (
                        women_distribution.get(count, 0)
                        + 1
                    )

                max_women_meetings = max(
                    women_opponent_counts.values()
                )

                women_pattern = (
                    tuple(
                        sorted(
                            women_distribution.items()
                        )
                    ),
                    max_women_meetings,
                )

                self.women_matrix_patterns[
                    women_pattern
                ] = (
                    self.women_matrix_patterns.get(
                        women_pattern,
                        0
                    )
                    + 1
                )

                # ------------------------------------------
                # 3.2.2 NUOVA PENALITÀ D×D
                # ------------------------------------------

                # Per ogni coppia D×D:
                #   0 = mai incontrate
                #   1 = incontro base
                #   2+ = incontri extra

                extra_counts = []

                for count in women_opponent_counts.values():

                    extra_counts.append(
                        max(0, count - 1)
                    )

                # Numero totale di incontri extra
                extra_total = sum(extra_counts)

                # Numero di coppie D×D
                number_of_pairs = len(extra_counts)

                # Penalità = scostamento dalla distribuzione
                # uniforme degli extra
                new_dd_penalty = sum(
                    abs(
                        extra * number_of_pairs
                        - extra_total
                    )
                    for extra in extra_counts
                )
                # ------------------------------------------
                # 3.2.2 FILTRO D×D - best penalita
                # ------------------------------------------

                if (
                    self.best_dd_penalty is None
                    or new_dd_penalty < self.best_dd_penalty
                ):

                    self.best_dd_penalty = new_dd_penalty
                    self.best_dd_solutions = 1

                    self.best_dd_solutions_data = [
                        selected_matches
                    ]

                elif new_dd_penalty == self.best_dd_penalty:

                    self.best_dd_solutions += 1

                    self.best_dd_solutions_data.append(
                        selected_matches
                    )
                
                # 3.2.2 Salviamo la nuova penalità

                self.new_uniformity_dd[
                    new_dd_penalty
                ] = (
                    self.new_uniformity_dd.get(
                        new_dd_penalty,
                        0
                    )
                    + 1
                )

               
                # ==========================================
                # 3.2.3 UOMO × UOMO
                # ==========================================

                men_counts = {}

                for match in selected_matches:

                    men = tuple(
                        sorted(
                            (
                                match.pair1.man,
                                match.pair2.man
                            )
                        )
                    )

                    if men[0] != men[1]:

                        men_counts[men] = (
                            men_counts.get(men, 0)
                            + 1
                        )

                # ------------------------------------------
                # 3.2.3 Penalità U×U
                # ------------------------------------------

                men_values = list(
                    men_counts.values()
                )

                men_penalty = None

                if men_values:

                    total = sum(men_values)
                    number_of_pairs = len(men_values)

                    men_penalty = sum(
                        abs(
                            value * number_of_pairs
                            - total
                        )
                        for value in men_values
                    )

                    self.uniformity_uu[
                        men_penalty
                    ] = (
                        self.uniformity_uu.get(
                            men_penalty,
                            0
                        )
                        + 1
                    )

                    if (
                        self.best_men_penalty is None
                        or men_penalty
                        < self.best_men_penalty
                    ):

                        self.best_men_penalty = (
                            men_penalty
                        )

                # ------------------------------------------
                # 3.2.3 Struttura U×U
                # ------------------------------------------

                men_opponent_counts = {}

                for match in selected_matches:

                    m1 = match.pair1.man
                    m2 = match.pair2.man

                    pair = tuple(
                        sorted((m1, m2))
                    )

                    men_opponent_counts[pair] = (
                        men_opponent_counts.get(pair, 0)
                        + 1
                    )

                # Tutte le possibili coppie U×U

                for i, m1 in enumerate(config.MEN):

                    for m2 in config.MEN[i + 1:]:

                        pair = tuple(
                            sorted((m1, m2))
                        )

                        if pair not in men_opponent_counts:

                            men_opponent_counts[pair] = 0

                men_distribution = {}

                for count in (
                    men_opponent_counts.values()
                ):

                    men_distribution[count] = (
                        men_distribution.get(count, 0)
                        + 1
                    )

                max_men_meetings = max(
                    men_opponent_counts.values()
                )

                men_pattern = (
                    tuple(
                        sorted(
                            men_distribution.items()
                        )
                    ),
                    max_men_meetings,
                )

                self.men_matrix_patterns[
                    men_pattern
                ] = (
                    self.men_matrix_patterns.get(
                        men_pattern,
                        0
                    )
                    + 1
                )

                # ==========================================
                # 3.2.4 UOMO × DONNA
                # ==========================================

                ud_counts = {}

                for match in selected_matches:

                    m1 = match.pair1.man
                    w1 = match.pair1.woman

                    m2 = match.pair2.man
                    w2 = match.pair2.woman

                    # Uomo 1 contro donna 2
                    # Uomo 2 contro donna 1

                    for man, woman in [
                        (m1, w2),
                        (m2, w1)
                    ]:

                        pair = (man, woman)

                        ud_counts[pair] = (
                            ud_counts.get(pair, 0)
                            + 1
                        )

                # ------------------------------------------
                # 3.2.4 Penalità U×D
                # ------------------------------------------

                ud_values = list(
                    ud_counts.values()
                )

                ud_penalty = None

                if ud_values:

                    total = sum(ud_values)
                    number_of_pairs = len(ud_values)

                    ud_penalty = sum(
                        abs(
                            value * number_of_pairs
                            - total
                        )
                        for value in ud_values
                    )

                    self.uniformity_ud[
                        ud_penalty
                    ] = (
                        self.uniformity_ud.get(
                            ud_penalty,
                            0
                        )
                        + 1
                    )

                # ------------------------------------------
                # 3.2.4 Struttura U×D
                # ------------------------------------------

                if ud_values:

                    ud_distribution = {}

                    for count in ud_values:

                        ud_distribution[count] = (
                            ud_distribution.get(
                                count,
                                0
                            )
                            + 1
                        )

                    max_ud_meetings = max(
                        ud_values
                    )

                    ud_pattern = (
                        tuple(
                            sorted(
                                ud_distribution.items()
                            )
                        ),
                        max_ud_meetings,
                    )

                    self.ud_matrix_patterns[
                        ud_pattern
                    ] = (
                        self.ud_matrix_patterns.get(
                            ud_pattern,
                            0
                        )
                        + 1
                    )

                # ==========================================
                # 3.2.5 COMBINAZIONE U×U / U×D
                # ==========================================

                if (
                    men_penalty is not None
                    and ud_penalty is not None
                ):

                    key = (
                        men_penalty,
                        ud_penalty
                    )

                    self.uu_ud_combinations[
                        key
                    ] = (
                        self.uu_ud_combinations.get(
                            key,
                            0
                        )
                        + 1
                    )

                # ==========================================
                # 3.2.6 SALVATAGGIO SOLUZIONE
                # ==========================================

                self.solutions_data.append({
                    "matches": selected_matches.copy(),
                    "dd_penalty": new_dd_penalty,
                    "uu_penalty": men_penalty,
                    "ud_penalty": ud_penalty,
                })

                # ==========================================
                # 3.2.7 LIMITE
                # ==========================================

                if (
                    self.count
                    >= self.max_solutions
                ):

                    self.stop_search()

        # ==================================================
        # 4. ESECUZIONE ENUMERAZIONE
        # ==================================================

        callback = SolutionCounter(
            self,
            model,
            max_solutions
        )

        solver = cp_model.CpSolver()

        solver.parameters.num_search_workers = 1

        # ==================================================
        # 5. Tutte le soluzioni
        # ==================================================

        status = solver.SearchForAllSolutions(
            model,
            callback
        )

        # ==================================================
        # 6. Filtro su Best DD penalty
        # ==================================================
        
        best_dd = min(
            solution["dd_penalty"]
            for solution in callback.solutions_data
        )

        dd_candidates = [
            solution
            for solution in callback.solutions_data
            if solution["dd_penalty"] == best_dd
        ]
        
        # ==================================================
        # 7. Filtro su Best DD penalty
        # ==================================================

        best_uu = min(
            solution["uu_penalty"]
            for solution in dd_candidates
        )
        
        # ==================================================
        # 8. Filtro su Best DD + UU penalty
        # ==================================================

        dd_uu_candidates = [
            solution
            for solution in dd_candidates
            if solution["uu_penalty"] == best_uu
        ]

        best_ud = min(
            solution["ud_penalty"]
            for solution in dd_uu_candidates
        )
        # ==================================================
        # 9. Soluzione finale 
        # ==================================================
        
        final_candidates = [
            solution
            for solution in dd_uu_candidates
            if solution["ud_penalty"] == best_ud
        ]

        final_solution = final_candidates[0]

        final_matches = final_solution["matches"]

        report_final_solution(
            self,
            final_matches
        )

        # ==================================================
        # 8. REPORT
        # ==================================================

        print("\n------------------------------------------")

        if callback.count >= max_solutions:

            print(
                f"Almeno {callback.count} "
                "soluzioni ottimali trovate."
            )

            print(
                "Enumerazione fermata al limite."
            )

        else:

            print(
                f"Soluzioni ottimali trovate: "
                f"{callback.count}"
            )

        print(
            f"Migliore uniformità U×U: "
            f"{callback.best_men_penalty}"
        )

        print("------------------------------------------")
        
        # ----------------------------------------------
        # 8.1 D×D
        # ----------------------------------------------
        
        print("\nUNIFORMITÀ DONNA × DONNA")
        print("------------------------------------------")

        for penalty, count in sorted(
            callback.new_uniformity_dd.items()
        ):

            print(
                f"Penalità {penalty:>4} : "
                f"{count} soluzioni"
            )

        print(
            f"\n Migliore uniformità D×D: "
            f"{callback.best_dd_penalty}"
        )

        print(
            f"Soluzioni con migliore D×D: "
            f"{callback.best_dd_solutions}"
        )
        
        print(
            f"\n Soluzioni candidate dopo filtro D×D: "
            f"{len(callback.best_dd_solutions_data)}"
        )
        
        print(
            f"Soluzioni salvate: "
            f"{len(callback.solutions_data)}"
        )

        print("------------------------------------------")

        # ----------------------------------------------
        # 8.2 U×U
        # ----------------------------------------------

        print("\nUNIFORMITÀ UOMO × UOMO")
        print("------------------------------------------")

        for penalty, count in sorted(
            callback.uniformity_uu.items()
        ):

            print(
                f"Penalità {penalty:>4} : "
                f"{count} soluzioni"
            )

        print(
            f"Migliore U×U tra le candidate D×D: "
            f"{best_uu}"
        )
        print("------------------------------------------")            
        # ----------------------------------------------
        # 8.3 U×D
        # ----------------------------------------------

        print("\nUNIFORMITÀ UOMO × DONNA")
        print("------------------------------------------")

        print(
            f"Candidate dopo U×U: "
            f"{len(dd_uu_candidates)}"
        )

        print(
            f"Migliore U×D tra le candidate D×D/U×U: "
            f"{best_ud}"
        )
        
        print(
            f"Penalità {best_ud:>3} : "
            f"{sum(
                1
                for solution in dd_uu_candidates
                if solution['ud_penalty'] == best_ud
            )} soluzioni"
        )
        print("------------------------------------------")

        print(
            f"Soluzioni finali: "
            f"{len(final_candidates)}"
        )
        
        # ----------------------------------------------
        # 8.4 COMBINAZIONI U×U / U×D
        # ----------------------------------------------

        #print("\nCOMBINAZIONI U×U / U×D")
        #print("------------------------------------------")

        #for (uu, ud), count in sorted(
        #    callback.uu_ud_combinations.items()
        #):

        #    print(
        #        f"U×U {uu:>3} | "
        #        f"U×D {ud:>3} : "
        #        f"{count} soluzioni"
        #    )

        # ----------------------------------------------
        # 8.5 STRUTTURA D×D
        # ----------------------------------------------

        print("\n TUTTE le STRUTTURE DONNA × DONNA")
        print("------------------------------------------")

        for pattern, count in sorted(
            callback.women_matrix_patterns.items()
        ):

            distribution, max_meetings = pattern

            print(
                f"Max incontri: {max_meetings} | "
                f"Distribuzione: "
                f"{dict(distribution)} "
                f"| Soluzioni: {count}"
            )

        # ----------------------------------------------
        # 8.6 STRUTTURA U×U
        # ----------------------------------------------

        print("\nTUTTE le STRUTTURA UOMO × UOMO")
        print("------------------------------------------")

        for pattern, count in sorted(
            callback.men_matrix_patterns.items()
        ):

            distribution, max_meetings = pattern

            print(
                f"Max incontri: {max_meetings} | "
                f"Distribuzione: "
                f"{dict(distribution)} "
                f"| Soluzioni: {count}"
            )
        # ----------------------------------------------
        # 8.7 STRUTTURA DELLE SOLUZIONI FINALI
        # ----------------------------------------------

        final_women_patterns = {}
        final_men_patterns = {}

        for solution in final_candidates:

            selected_matches = solution["matches"]

            # ==========================================
            # D × D
            # ==========================================

            women_counts = {}

            for match in selected_matches:

                w1 = match.pair1.woman
                w2 = match.pair2.woman

                pair = tuple(sorted((w1, w2)))

                women_counts[pair] = (
                    women_counts.get(pair, 0) + 1
                )

            for i, w1 in enumerate(config.WOMEN):

                for w2 in config.WOMEN[i + 1:]:

                    pair = tuple(sorted((w1, w2)))

                    if pair not in women_counts:
                        women_counts[pair] = 0

            distribution = {}

            for count in women_counts.values():

                distribution[count] = (
                    distribution.get(count, 0) + 1
                )

            max_meetings = max(women_counts.values())

            pattern = (
                tuple(sorted(distribution.items())),
                max_meetings,
            )

            final_women_patterns[pattern] = (
                final_women_patterns.get(pattern, 0) + 1
            )

            # ==========================================
            # U × U
            # ==========================================

            men_counts = {}

            for match in selected_matches:

                m1 = match.pair1.man
                m2 = match.pair2.man

                pair = tuple(sorted((m1, m2)))

                if m1 != m2:

                    men_counts[pair] = (
                        men_counts.get(pair, 0) + 1
                    )

            for i, m1 in enumerate(config.MEN):

                for m2 in config.MEN[i + 1:]:

                    pair = tuple(sorted((m1, m2)))

                    if pair not in men_counts:
                        men_counts[pair] = 0

            distribution = {}

            for count in men_counts.values():

                distribution[count] = (
                    distribution.get(count, 0) + 1
                )

            max_meetings = max(men_counts.values())

            pattern = (
                tuple(sorted(distribution.items())),
                max_meetings,
            )

            final_men_patterns[pattern] = (
                final_men_patterns.get(pattern, 0) + 1
            )


        print("\n## STRUTTURA D×D DELLE SOLUZIONI FINALI")
        print("------------------------------------------")

        for pattern, count in sorted(final_women_patterns.items()):

            distribution, max_meetings = pattern

            print(
                f"Max incontri: {max_meetings} | "
                f"Distribuzione: {dict(distribution)} | "
                f"Soluzioni: {count}"
            )


        print("\n## STRUTTURA U×U DELLE SOLUZIONI FINALI")
        print("------------------------------------------")

        for pattern, count in sorted(final_men_patterns.items()):

            distribution, max_meetings = pattern

            print(
                f"Max incontri: {max_meetings} | "
                f"Distribuzione: {dict(distribution)} | "
                f"Soluzioni: {count}"
            )



        # ----------------------------------------------
        # 8.8 STRUTTURA U×D
        # ----------------------------------------------

        #print("\nSTRUTTURA UOMO × DONNA")
        #print("------------------------------------------")

        #for pattern, count in sorted(
        #    callback.ud_matrix_patterns.items()
        #):

        #    distribution, max_meetings = pattern

        #    print(
        #        f"Max incontri: {max_meetings} | "
        #        f"Distribuzione: "
        #        f"{dict(distribution)} "
        #        f"| Soluzioni: {count}"
        #    )

        return (
            final_matches,
            callback.count,
            len(callback.best_dd_solutions_data),
            len(dd_uu_candidates),
            len(final_candidates)
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

        optimal_objective = solver.ObjectiveValue()

        print(
            f"\nObiettivo ottimale rilevato: {optimal_objective}"
        )
        
        (
            final_matches,
            optimal_solutions,
            dd_solutions,
            uu_solutions,
            final_solutions
        ) = self.enumerate_optimal_solutions(
            optimal_objective,
            max_solutions=100
        )


        return (
            solver,
            final_matches,
            optimal_solutions,
            dd_solutions,
            uu_solutions,
            final_solutions
        )

