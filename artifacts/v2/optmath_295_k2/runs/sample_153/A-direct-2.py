import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_peaks - 1)
    model.A = pyo.RangeSet(0, num_amino_acids - 1)

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][a] * m.x[p, a] for p in m.P for a in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.peak_con = pyo.Constraint(
        model.P, rule=lambda m, p: sum(m.x[p, a] for a in m.A) <= 1
    )
    model.aa_con = pyo.Constraint(
        model.A, rule=lambda m, a: sum(m.x[p, a] for p in m.P) <= 1
    )
    model.total_con = pyo.Constraint(
        rule=lambda m: sum(m.x[p, a] for p in m.P for a in m.A) == num_assignments
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}