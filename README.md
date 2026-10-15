# Python Mini-Projects: Weather Forecast & Population Modeling

This repository contains two data analysis and modeling mini-projects built with modular Python, Jupyter Notebooks, and Pytest.

---

## Project Structure

```text
.
├── src/
│   ├── __init__.py
│   ├── utils.py               # Reusable utility functions (RNG seed generator)
│   ├── project1.py            # API request logic (Open-Meteo Geocoding & Forecast)
│   └── project2.py            # OOP Domain Models (City & PopulationSimulator)
├── tests/
│   ├── __init__.py
│   ├── test_project1.py       # Unit & integration tests for API module
│   └── test_project2.py       # Unit tests for OOP domain classes & seeds
├── project1_population.ipynb  # Mini-Project 1: API Weather Forecast
├── project2_population.ipynb  # Mini-Project 2: Population OOP Simulation
├── requirements.txt           # Project dependencies
├── pytest.ini                 # Test configuration
└── README.md
```

---

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <YOUR-GITHUB-REPO-LINK>
   cd <YOUR-REPO-FOLDER>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run

### 1. Execute Unit Tests
To verify all test suites and mock behavior, run:
```bash
python -m pytest -v
```

### 2. Launch Notebooks
Launch Jupyter Notebook to view interactive analysis and visualization:
```bash
jupyter notebook
```
Open either `project1_population.ipynb` or `project2_population.ipynb` and select **Kernel → Restart & Run All**.

---

## Summary of Findings

### Mini-Project 1: Weather Forecast via Web API
* Successfully resolved location names into precise coordinates using the Open-Meteo Geocoding API.
* Extracted and formatted 7-day temperature, precipitation, and wind forecasts into clean Pandas DataFrames.
* Visualized multi-day trends with reproducible charts.

### Mini-Project 2: Object-Oriented Population Simulation
* Modeled domain entities (`City` and `PopulationSimulator`) with proper encapsulation, type hints, docstrings, and custom dunder methods (`__repr__`, `__str__`, `__len__`, `__getitem__`).
* Ensured complete execution reproducibility across simulation runs using NumPy's `default_rng(seed)`.
* Analyzed variance in multi-year growth trajectories under stochastic environmental shifts.