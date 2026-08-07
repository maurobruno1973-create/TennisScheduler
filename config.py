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

    ("Graeme", "Beth"),
    ("Graeme", "Matilde"),
    ("Graeme", "Maryna"),

    ("Quentin", "Tiantian"),
    ("Quentin", "Maryna"),
    ("Quentin", "Matilde"),

    ("Mauro", "Beth"),
    ("Mauro", "Paola"),
    ("Mauro", "Lina"),
]

# Vincoli principali
TARGET_MATCHES_PER_WOMAN = 6

# Preferenze (non vincoli rigidi)

# Coppie di giocatori che si preferisce NON far incontrare
# come avversari.
SOFT_AVOID_OPPONENTS = [
    ("Graeme", "Paola"),
]

MAXIMIZE_DIFFERENT_OPPONENTS = True
MINIMIZE_REMATCHES = True
BALANCE_MEN = True

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
