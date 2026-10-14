import numpy as np

def get_rng(seed: int = 42) -> np.random.Generator:
    """Returns a seeded NumPy random generator for reproducible results."""
    return np.random.default_rng(seed)
