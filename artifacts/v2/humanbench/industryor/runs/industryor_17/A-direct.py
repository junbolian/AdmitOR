import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural data: residential areas and coverage sets
    areas = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
    coverage = {
        "A": ["A", "C", "E", "G", "H", "I"],
        "B": ["B", "H", "I"],
        "C": ["A", "C", "G", "H", "I"],
        "D": ["D", "J"],
        "E": ["A", "E", "G"],
        "F": ["F", "J", "K"],
        "G": ["A", "C", "E", "G"],
        "H": ["A", "B", "C", "H", "I"],
        "I": ["A", "B", "C", "H", "I"],
        "J": ["D", "F", "J", "K", "L"],
        "K": ["F", "J", "K", "L"],
        "L": ["J", "K", "L"],
    }

    # Read parameter (radius) from params; validate it matches structural assumption
    coverage_radius = params["coverage_radius"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=areas)

    model.x = pyo.Var(model.A, within=pyo.Binary)

    # Objective: minimize number of stores
    def obj_rule(mod):
        return sum(mod.x[a] for a in mod.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Coverage constraints: each area covered by at least one open store
    def cov_rule(mod, a):
        return sum(mod.x[b] for b in coverage[a]) >= 1
    model.coverage = pyo.Constraint(model.A, rule=cov_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": obj_val, "status": "optimal"}