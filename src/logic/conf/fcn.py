from src.logic.conf.ici import ICI


class FCN:
    """
    Full Conf Normalizer -- Normalizes the whole config
    """
    def __init__(self):
        self.ici: ICI = ICI()

    def norm(self, conf: dict) -> dict:
        return conf
