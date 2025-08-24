from box import Box


class ICI:
    """
    Ingrain Config Interpreter -- Transforms configs according to the ingrain configuration
    # TODO: I have to decide the ingrain syntax to finish
    # consider a mere transformation vs interpretation - together or separate
    """
    def __init__(self, ingrains: dict = None):
        self.ingrains = ingrains

    @property
    def ingrains(self) -> Box:
        return self._ingrains

    @ingrains.setter
    def ingrains(self, ingrains: dict | Box) -> None:
        self._ingrains = Box(ingrains or {})
