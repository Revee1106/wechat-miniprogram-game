class DwellingService:
    def get_breakthrough_bonus(self, dwelling_level: int) -> float:
        return min(0.02 * max(dwelling_level - 1, 0), 0.10)
