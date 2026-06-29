from abc import ABC, abstractmethod
import numpy as np


class BaseSimulator(ABC):
    """
    Parent class for all microstructure simulators.

    It will eventually contain functionality that is shared between Iron, Steel and Case Iron simulators.

                    BaseSimulator
                     ▲
        ┌────────────┼────────────┐
        │            │            │
      Iron         Steel      Cast Iron
    """

    def __init__(self, carbon_percent, width=400, height=300, n_grains=50, seed=42):
        self.carbon_percent = carbon_percent
        self.width = width
        self.height = height
        self.n_grains = n_grains
        self.seed = seed

    @abstractmethod
    def get_phase_state(self, temperature):
        raise NotImplementedError
    
    @abstractmethod
    def generate_microstructure(self, temperature):
        raise NotImplementedError
    
    def get_grain_boundaries(self, grain_map):
        boundary = np.zeros_like(grain_map, dtype=bool)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            shifted = np.roll(np.roll(grain_map, dx, axis=1), dy, axis=0)
            boundary |= (grain_map != shifted)
        return boundary
    
    def describe(self):
        # return f"{self.__class__.__name__}(C={self.carbon_percent}%, {self.width}x{self.height}px, seed={self.seed})" # original
        return f"{self.__class__.__name__}( C={self.carbon_percent}%)" 