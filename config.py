"""
Configurazione del torneo
Modifica solo questo file se cambiano coppie o parametri.
"""

# Numero di partite da selezionare
NUM_MATCHES = 18

# Coppie disponibili (Uomo, Donna)
PAIRS = [
    ("Ash", "Tiantian"),
    ("Ash", "Lina"),
    ("Ash", "Maryna"),

    ("Graeme", "Beth"),
    ("Graeme", "Matilde"),
    ("Graeme", "Maryna"),

    ("Quentin", "Tiantian"),
    ("Quentin", "Matilde"),
    ("Quentin", "Paola"),

    ("Mauro", "Beth"),
    ("Mauro", "Paola"),
    ("Mauro", "Lina"),
]

# Vincoli principali
ENFORCE_EQUAL_PAIR_MATCHES = True

# Preferenze (non vincoli rigidi)

# Coppie di giocatori che si preferisce NON far incontrare
# come avversari.
SOFT_AVOID_OPPONENTS = [
    ("Graeme", "Paola"),
]

MAXIMIZE_DIFFERENT_OPPONENTS = True
BALANCE_MEN = True

OBJECTIVE_WEIGHTS = {
    "WOMEN_BALANCE": 100,
    "MEN_BALANCE": 50,
    "SOFT_AVOID_OPPONENTS": 10,
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

# ==================================================
# TIER DONNE
# ==================================================
USE_WOMEN_TIERS = True

WOMEN_TIERS = {

    # Tier 1
    "Beth": 1,
    "Paola": 1,

    # Tier 2
    "Tiantian": 2,

    # Tier 3
    "Lina": 3,
    "Maryna": 3,
    "Matilde": 3,
}
