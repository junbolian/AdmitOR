import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    peaks = list(range(num_peaks))
    acids = list(range(num_amino_acids))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=peaks)
    model.A = pyo.Set(initialize=acids)

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][a] * m.x[p, a] for p in m.P for a in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(m, p):
        return sum(m.x[p, a] for a in m.A) <= 1

    model.peak_constraint = pyo.Constraint(model.P, rule=peak_rule)

    def acid_rule(m, a):
        return sum(m.x[p, a] for p in m.P) <= 1

    model.acid_constraint = pyo.Constraint(model.A, rule=acid_rule)

    def total_rule(m):
        return sum(m.x[p, a] for p in m.P for a in m.A) == num_assignments

    model.total_constraint = pyo.Constraint(rule=total_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}