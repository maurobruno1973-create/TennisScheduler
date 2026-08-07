from scheduler import TournamentScheduler


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
