"""
Tennis Scheduler
Enumerazione delle soluzioni ottimali.
"""

import config


from ortools.sat.python import cp_model

from tier_evaluation import evaluate_final_candidates

def enumerate_optimal_solutions(
    scheduler,
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

        model = scheduler.model.clone()

        # Ricostruiamo l'espressione dell'obiettivo
        objective = 0

        objective += (
            config.OBJECTIVE_WEIGHTS["WOMEN_BALANCE"]
            * sum(scheduler.women_deviation_vars.values())
        )

        objective += (
            config.OBJECTIVE_WEIGHTS["MEN_BALANCE"]
            * sum(scheduler.men_deviation_vars.values())
        )

        objective += (
            config.OBJECTIVE_WEIGHTS["SOFT_AVOID_OPPONENTS"]
            * sum(scheduler.soft_avoid_vars)
        )

        objective -= (
            config.OBJECTIVE_WEIGHTS["DIFFERENT_OPPONENTS"]
            * sum(scheduler.opponent_played_vars.values())
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
            scheduler,
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
        
        if config.USE_WOMEN_TIERS:

            # ==================================================
            # TIER → PARETO → SCELTA UTENTE
            # ==================================================

            pareto_candidates = evaluate_final_candidates(
                final_candidates
            )

            print("\n=== SELEZIONE SOLUZIONE ===")

            print(
                f"\nSono disponibili {len(pareto_candidates)} "
                "soluzioni Pareto.\n"
            )

            for index, candidate in enumerate(
                pareto_candidates,
                start=1
            ):

                print(
                    f"[{index}] "
                    f"P{candidate['solution_number']} → "
                    f"M1: {candidate['method1']} | "
                    f"M2: {candidate['method2']}"
                )

            while True:

                choice = input(
                    f"\nSeleziona la soluzione da utilizzare "
                    f"[1-{len(pareto_candidates)}]: "
                )

                try:

                    choice = int(choice)

                    if 1 <= choice <= len(pareto_candidates):
                        break

                    print(
                        f"Scelta non valida. Inserisci un numero "
                        f"tra 1 e {len(pareto_candidates)}."
                    )

                except ValueError:

                    print("Inserisci un numero valido.")

            selected_candidate = pareto_candidates[choice - 1]

            final_solution = selected_candidate["solution"]

        else:

            # ==================================================
            # SENZA TIER → SELEZIONE AUTOMATICA
            # ==================================================

            final_solution = final_candidates[0]

        final_matches = final_solution["matches"]

        # ==================================================
        # 10. REPORT
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
        # 10.1 D×D
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
        # 10.2 U×U
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
        # 10.3 U×D
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
        # 10.4 COMBINAZIONI U×U / U×D
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
        # 10.5 STRUTTURA D×D
        # ----------------------------------------------

        #print("\n TUTTE le STRUTTURE DONNA × DONNA")
        #print("------------------------------------------")

        #for pattern, count in sorted(
        #    callback.women_matrix_patterns.items()
        #):

        #    distribution, max_meetings = pattern

        #    print(
        #        f"Max incontri: {max_meetings} | "
        #        f"Distribuzione: "
        #        f"{dict(distribution)} "
        #        f"| Soluzioni: {count}"
        #    )

        # ----------------------------------------------
        # 10.6 STRUTTURA U×U
        # ----------------------------------------------

        #print("\nTUTTE le STRUTTURA UOMO × UOMO")
        #print("------------------------------------------")

        #for pattern, count in sorted(
        #    callback.men_matrix_patterns.items()
        #):

        #    distribution, max_meetings = pattern

        #    print(
        #        f"Max incontri: {max_meetings} | "
        #        f"Distribuzione: "
        #        f"{dict(distribution)} "
        #        f"| Soluzioni: {count}"
        #    )


        # ==============================
        # 10.7 RISULTATO del PARETO
        # ==============================
        
        if config.USE_WOMEN_TIERS:
            print(
                "\n=== PARETO CANDIDATES ==="
            )

            for candidate in pareto_candidates:

                solution_number = candidate["solution_number"]

                print(
                    f"\nP{solution_number} → "
                    f"M1: {candidate['method1']} | "
                    f"M2: {candidate['method2']}\n"
                )

                for man in config.MEN:

                    tier_counts = candidate["tier_counts"][man]
                    print(
                    f"{man}: "
                    f"T1={tier_counts[1]} "
                    f"T2={tier_counts[2]} "
                    f"T3={tier_counts[3]}"
                    )

                delta_distribution = candidate["delta_distribution"]

                print("\nM2:"
                    f"Δ0={delta_distribution[0]} | "
                    f"Δ1={delta_distribution[1]} | "
                    f"Δ2={delta_distribution[2]}"
                )

                print(
                    f"Differenza totale={candidate['method2']}"
                )
           
               
        # ----------------------------------------------
        # 10.8 STRUTTURA DELLE SOLUZIONI FINALI
        # ----------------------------------------------
        print("\n=== ANALISI SOLUZIONI FINALI ===")
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
