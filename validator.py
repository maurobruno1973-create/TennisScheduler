import config


def validate_solution(
    scheduler,
    solver
):

    print("\n=== VERIFICA SOLUZIONE ===")

    errors = []

    # ----------------------------------
    # Numero di partite
    # ----------------------------------

    selected_matches = [
        i
        for i, var in scheduler.match_vars.items()
        if solver.Value(var)
    ]

    selected_count = len(selected_matches)

    print(
        f"Partite selezionate       : "
        f"{selected_count} / {config.NUM_MATCHES}",
        end=""
    )

    if selected_count == config.NUM_MATCHES:
        print("   OK")
    else:
        print("   ERRORE")
        errors.append("Numero partite errato")

    # ----------------------------------
    # Partite duplicate
    # ----------------------------------

    unique_matches = set()

    for i in selected_matches:

        match = scheduler.matches[i]

        pair1 = str(match.pair1)
        pair2 = str(match.pair2)

        key = tuple(sorted((pair1, pair2)))

        unique_matches.add(key)

    duplicates = selected_count - len(unique_matches)

    print(
        f"Partite duplicate         : "
        f"{duplicates}",
        end=""
    )

    if duplicates == 0:
        print("   OK")
    else:
        print("   ERRORE")
        errors.append("Partite duplicate")

    # ----------------------------------
    # Partite per donna
    # ----------------------------------

    print("\nPARTITE PER DONNA")

    for woman in config.WOMEN:

        count = 0

        for i in selected_matches:

            match = scheduler.matches[i]

            players = (
                list(match.pair1.players)
                + list(match.pair2.players)
            )

            if woman in players:
                count += 1

        print(
            f"{woman:25}: {count}",
            end=""
        )

        if count == config.TARGET_MATCHES_PER_WOMAN:
            print("   OK")
        else:
            print("   ERRORE")
            errors.append(
                f"Numero partite errato per {woman}"
            )

    # ----------------------------------
    # Partite per uomo
    # ----------------------------------

    print("\nPARTITE PER UOMO")

    for man in config.MEN:

        count = 0

        for i in selected_matches:

            match = scheduler.matches[i]

            players = (
                list(match.pair1.players)
                + list(match.pair2.players)
            )

            if man in players:
                count += 1

        target = scheduler.target_men_matches

        deviation = abs(count - target)

        print(
            f"{man:25}: {count} "
            f"(target {target}, deviazione {deviation})"
        )

    # ----------------------------------
    # Giocatore contro se stesso
    # ----------------------------------

    self_match_errors = 0

    for i in selected_matches:

        match = scheduler.matches[i]

        team1 = set(match.pair1.players)
        team2 = set(match.pair2.players)

        if team1 & team2:
            self_match_errors += 1

    print(
        f"\nGiocatori contro se stessi: "
        f"{self_match_errors}",
        end=""
    )

    if self_match_errors == 0:
        print("   OK")
    else:
        print("   ERRORE")
        errors.append(
            "Giocatori contro se stessi"
        )

    # ----------------------------------
    # Incontri indesiderati
    # ----------------------------------

    soft_avoid_count = 0

    for var in scheduler.soft_avoid_vars:

        if solver.Value(var):
            soft_avoid_count += 1

    print(
        f"Incontri indesiderati     : "
        f"{soft_avoid_count}"
    )

    # ----------------------------------
    # Avversari diversi
    # ----------------------------------

    different_opponents = sum(
        solver.Value(var)
        for var in scheduler.opponent_played_vars.values()
    )

    print(
        f"Avversari diversi         : "
        f"{different_opponents}"
    )

    # ----------------------------------
    # Risultato finale
    # ----------------------------------

    print("\n==========================================")

    if errors:

        print("VERIFICA FINALE: ERRORE")

        for error in errors:
            print(f" - {error}")

    else:

        print("VERIFICA FINALE: OK")

    print("==========================================")
