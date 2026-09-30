CURRENT_CHEMIST_ID = 1


class CurrentChemist:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.chemist_id = CURRENT_CHEMIST_ID
        return cls._instance


def get_current_chemist_id() -> int:
    return CurrentChemist().chemist_id
