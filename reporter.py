import config


def report_solution(scheduler, solver):

    print("=== CONTRIBUTO FUNZIONE OBIETTIVO ===")

    men_balance = (
        config.OBJECTIVE_WEIGHTS["MEN_BALANCE"]
        * sum(
            solver.Value(var)
            for var in scheduler.men_deviation_vars.values()
        )
    )

    soft_avoid = (
        config.OBJECTIVE_WEIGHTS["SOFT_AVOID_OPPONENTS"]
        * sum(
            solver.Value(var)
            for var in scheduler.soft_avoid_vars
        )
    )

    different_opponents = (
        config.OBJECTIVE_WEIGHTS["DIFFERENT_OPPONENTS"]
        * sum(
            solver.Value(var)
            for var in scheduler.opponent_played_vars.values()
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

    # ----------------------------------
    # Partite selezionate
    # ----------------------------------

    print("=== PARTITE SELEZIONATE ===")

    count = 1

    for i, match in enumerate(scheduler.matches):

        if solver.Value(scheduler.match_vars[i]):

            print(f"{count:2d}. {match}")

            count += 1

    # ----------------------------------
    # Partite per giocatore
    # ----------------------------------

    print("\n=== PARTITE PER GIOCATORE ===")

    for player in sorted(scheduler.player_count_vars):

        print(
            f"{player:10} "
            f"{solver.Value(scheduler.player_count_vars[player])}"
        )

    # ----------------------------------
    # Avversari diversi
    # ----------------------------------

    print("\n=== AVVERSARI DIVERSI ===")

    for player in sorted(scheduler.player_count_vars):

        opponents = set()

        for (p1, p2), played_var in (
            scheduler.opponent_played_vars.items()
        ):

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

    # ----------------------------------
    # Deviazione uomini
    # ----------------------------------

    print("\n=== DEVIAZIONE UOMINI ===")

    total = 0

    for man in config.MEN:

        dev = solver.Value(
            scheduler.men_deviation_vars[man]
        )

        print(f"{man:10} {dev}")

        total += dev

    print("----------------------")
    print(f"Totale      {total}")
