from dataclasses import dataclass


@dataclass(frozen=True)
class Pair:
    man: str
    woman: str

    @property
    def players(self):
        return {self.man, self.woman}

    def __str__(self):
        return f"{self.man} - {self.woman}"


@dataclass(frozen=True)
class Match:
    pair1: Pair
    pair2: Pair

    @property
    def players(self):
        return self.pair1.players | self.pair2.players

    def is_valid(self):
        return len(self.players) == 4

    def __str__(self):
        return f"{self.pair1}   vs   {self.pair2}"
