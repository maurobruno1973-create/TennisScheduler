import config


def evaluate_final_candidates(final_candidates):

    tier_results = []

    for solution_number, solution in enumerate(
        final_candidates,
        start=1
    ):

        matches = solution["matches"]
        all_tier_counts = {}

        # ==================================================
        # METODO 1
        # Uniformità delle avversarie per uomo
        # ==================================================

        #print("\nMetodo 1 - Uniformità avversarie")
        
        total_spread = 0
        
        for man in config.MEN:

            tier_counts = {
                1: 0,
                2: 0,
                3: 0
            }

            for match in matches:

                # Uomo nella coppia 1
                if match.pair1.man == man:

                    woman = match.pair2.woman

                    tier = config.WOMEN_TIERS.get(woman)

                    if tier is not None:
                        tier_counts[tier] += 1

                # Uomo nella coppia 2
                elif match.pair2.man == man:

                    woman = match.pair1.woman

                    tier = config.WOMEN_TIERS.get(woman)

                    if tier is not None:
                        tier_counts[tier] += 1

            # Calcolo uniformità dell'uomo
            values = list(
                tier_counts.values()
            )

            # Salviamo distribuzione di questo uomo
            all_tier_counts[man] = tier_counts.copy()

            spread = max(values) - min(values)
            total_spread += spread
   
        # ==================================================
        # METODO 2
        # Equilibrio delle singole partite
        # ==================================================

        #print("\nMetodo 2 - Equilibrio partite")

        difference_distribution = {
            0: 0,
            1: 0,
            2: 0
        }

        total_difference = 0

        for match_number, match in enumerate(
            matches,
            start=1
        ):
                                                
            woman1 = match.pair1.woman
            woman2 = match.pair2.woman

            tier1 = config.WOMEN_TIERS.get(woman1)
            tier2 = config.WOMEN_TIERS.get(woman2)

            if tier1 is None or tier2 is None:
                continue

            difference = abs(
                tier1 - tier2
            )

            difference_distribution[
                difference
            ] += 1

            total_difference += difference

        tier_results.append({
            "solution": solution,
            "method1": total_spread,
            "method2": total_difference,
            "tier_counts": all_tier_counts,
            "delta_distribution": difference_distribution,
            "solution_number": solution_number,
        })


    # ==================================================
    # Pareto candidati M1/M2
    # ==================================================

    pareto_candidates = []

    for candidate in tier_results:

        dominated = False

        for other in tier_results:

            if candidate is other:
                continue

            better_or_equal_m1 = (
                other["method1"]
                <= candidate["method1"]
            )

            better_or_equal_m2 = (
                other["method2"]
                <= candidate["method2"]
            )

            strictly_better = (
                other["method1"]
                < candidate["method1"]
                or
                other["method2"]
                < candidate["method2"]
            )

            if (
                better_or_equal_m1
                and better_or_equal_m2
                and strictly_better
            ):
                dominated = True
                break

        if not dominated:
            pareto_candidates.append(candidate)

    return pareto_candidates
