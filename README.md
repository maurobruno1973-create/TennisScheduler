# TennisScheduler

Tournament scheduler for mixed doubles tennis tournaments.

The program generates valid matches between predefined mixed doubles pairs
and uses Google OR-Tools CP-SAT to select the optimal set of matches according
to configurable constraints and objectives.

---

## Main features

The scheduler currently handles:

- generation of valid mixed doubles matches;
- elimination of duplicate matches;
- configurable number of matches to select;
- equal number of matches for women;
- balanced number of matches for men;
- soft penalties for undesirable encounters;
- maximisation of different opponents;
- validation of the final solution;
- automatic generation of an Excel report.

The program is designed to remain generic and configurable for tournaments
with different numbers of players and different requirements.

---

## Project structure

```text
TennisScheduler/
│
├── config.py
├── models.py
├── match_generator.py
├── scheduler.py
├── reporter.py
├── validator.py
├── excel_reporter.py
├── main.py
├── requirements.txt
└── README.md

config.py

Contains the tournament configuration, including:

players;
men and women;
available pairs;
number of matches;
objective weights;
other configurable parameters.

The scheduling logic should not normally need to be modified when changing
the tournament configuration.

models.py

Contains the main data models:

Pair
Match

Match also validates that the four players in a match are distinct.

match_generator.py

Generates all valid matches from the available pairs.

Invalid matches and duplicate matches are excluded.

scheduler.py

Contains the main CP-SAT optimisation model.

It creates:

match selection variables;
player counters;
target/deviation variables;
opponent variables;
soft-avoid variables;
objective function;
tournament constraints.
reporter.py

Produces the textual report in the console, including:

objective function contribution;
selected matches;
matches per player;
different opponents;
men's deviations.
validator.py

Performs the final validation of the generated solution.

It checks, among other things:

number of selected matches;
duplicate matches;
matches per woman;
matches per man;
players against themselves;
undesirable encounters;
different opponents.

The expected final message is:

==========================================
VERIFICA FINALE: OK
==========================================
excel_reporter.py

Generates the final Excel report:

TennisScheduler_Result.xlsx

The workbook contains four sheets:

Riepilogo
Partite
Giocatori
Avversari

The Excel file is intended to be the user-facing result of the tournament
scheduler.

main.py

Entry point of the application.

It creates the scheduler, builds the model, solves the tournament and
generates the Excel report.

Requirements

The required Python packages are listed in:

requirements.txt

Main dependencies:

OR-Tools
pandas
openpyxl

Running the program in Google Colab

The recommended workflow is to start from a new Colab notebook.

1. Clone the repository

Run:

!git clone https://github.com/maurobruno1973-create/TennisScheduler.git
2. Install the requirements

Run:

!pip install -r /content/TennisScheduler/requirements.txt

If Colab asks to restart the runtime after installation,
restart the runtime before continuing.

This warning can occur because Colab may already have imported packages
with different versions.

3. Run the scheduler

Run:

!python /content/TennisScheduler/main.py

The program will:

generate the available matches;
build the optimisation model;
calculate the tournament targets;
add the constraints;
optimise the selected matches;
validate the solution;
generate the Excel report.
Output

A successful execution should end with:

VERIFICA FINALE: OK

and create:

TennisScheduler_Result.xlsx

The Excel file contains the final tournament schedule and statistics.

Configuration

Tournament-specific settings should normally be changed in:

config.py

Examples include:

players;
available mixed doubles pairs;
number of matches;
objective weights;
other tournament parameters.

The scheduler itself should remain unchanged whenever possible.

Objective function

The current optimisation considers three main components.

Men's balance

Keeps the number of matches played by the men as balanced as possible.

This is implemented as a weighted objective so that the model remains
generic when the number of men changes.

Soft avoidances

Some encounters can be marked as undesirable.

These are treated as soft constraints and therefore can be accepted if
necessary to obtain a better overall solution.

Different opponents

The model rewards players for facing a larger number of different opponents.

This is implemented as an objective component after duplicate matches have
been eliminated.

Match duplicates

A match is considered identical regardless of the order of the two opposing
pairs.

For example:

AB vs CD

and

CD vs AB

represent the same match.

Duplicate matches are therefore eliminated during match generation.

Sessions

Session scheduling is currently not part of the optimisation model.

This is intentional.

The current scheduler selects the tournament matches without imposing
session-specific constraints.

Session scheduling may be added as a separate feature in the future if
required.

Development status

Current version: v0.12

Current status:

tournament optimisation: complete;
solution validation: complete;
modular project structure: complete;
GitHub/Colab workflow: tested;
Excel report generation: complete.

Future improvements may include:

optional session scheduling;
additional tournament constraints;
further Excel presentation improvements;
additional testing with different tournament configurations.
