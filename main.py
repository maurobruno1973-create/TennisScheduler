from scheduler import TournamentScheduler
from excel_reporter import create_excel_report

if __name__ == "__main__":

    scheduler = TournamentScheduler()
    scheduler.generate_matches()
    scheduler.check_pair_distribution()
    
    scheduler.build_model()
    scheduler.build_player_counters()
    scheduler.build_player_count_variables()
    scheduler.compute_targets()

    scheduler.build_women_deviation_variables()
    scheduler.build_men_deviation_variables()
    scheduler.build_soft_avoid_variables()
    scheduler.build_opponent_count_variables()
    scheduler.build_opponent_played_variables()

    scheduler.add_opponent_count_constraints()
    scheduler.add_opponent_played_constraints()
    scheduler.add_basic_constraints()
    scheduler.add_objective()

    (
        solver,
        final_matches,
        optimal_solutions,
        dd_solutions,
        uu_solutions,
        final_solutions
    ) = scheduler.solve()

    create_excel_report(
        scheduler,
        solver,
        final_matches,
        optimal_solutions,
        dd_solutions,
        uu_solutions,
        final_solutions
    )
