"""
Configurazione del torneo
Modifica solo questo file se cambiano coppie o parametri.
"""

# Numero di partite da selezionare
NUM_MATCHES = 24

# Coppie disponibili (Uomo, Donna)
PAIRS = [
    ("Ash", "Tiantian"),
    ("Ash", "Lina"),
    ("Ash", "Maryna"),

    ("Graeme", "Beth"),
    ("Graeme", "Matilde"),
    ("Graeme", "Maryna"),

    ("Quentin", "Tiantian"),
    ("Quentin", "Maryna"),
    ("Quentin", "Paola"),

    ("Mauro", "Beth"),
    ("Mauro", "Paola"),
    ("Mauro", "Lina"),
]

# Vincoli principali

# Preferenze (non vincoli rigidi)

# Coppie di giocatori che si preferisce NON far incontrare
# come avversari.
SOFT_AVOID_OPPONENTS = [
    ("Graeme", "Paola"),
]

MAXIMIZE_DIFFERENT_OPPONENTS = True
BALANCE_MEN = True

OBJECTIVE_WEIGHTS = {
    "MEN_BALANCE": 100,
    "SOFT_AVOID_OPPONENTS": 50,
    "DIFFERENT_OPPONENTS": 1,
}

# Giocatori

MEN = [
    "Ash",
    "Graeme",
    "Quentin",
    "Mauro",
]

WOMEN = [
    "Beth",
    "Lina",
    "Maryna",
    "Matilde",
    "Paola",
    "Tiantian",
]
