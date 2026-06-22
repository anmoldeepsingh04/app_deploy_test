class BaseSimulator:
    """
    Parent class for all microstructure simulators.

    It will eventually contain functionality that is shared between Iron, Steel and Case Iron simulators.

                    BaseSimulator
                     ▲
        ┌────────────┼────────────┐
        │            │            │
      Iron         Steel      Cast Iron
    """

    def __init__(self):
        pass