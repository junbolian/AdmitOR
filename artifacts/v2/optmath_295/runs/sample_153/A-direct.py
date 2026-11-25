import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    peak_capacity = params["peak_capacity"]
    amino_acid_capacity = params["amino_acid_capacity"]

    num_peaks = len(cost)
    num_amino_acids = len(cost[0])

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, num_peaks - 1)
    model.AMINO_ACIDS = pyo.RangeSet(0, num_amino_acids - 1)

    model.x = pyo.Var(model.PEAKS, model.AMINO_ACIDS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][a] * m.x[p, a] for p in m.PEAKS for a in m.AMINO_ACIDS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_cap_rule(m, p):
        return sum(m.x[p, a] for a in m.AMINO_ACIDS) <= peak_capacity

    model.peak_cap = pyo.Constraint(model.PEAKS, rule=peak_cap_rule)

    def aa_cap_rule(m, a):
        return sum(m.x[p, a] for p in m.PEAKS) <= amino_acid_capacity

    model.aa_cap = pyo.Constraint(model.AMINO_ACIDS, rule=aa_cap_rule)

    def total_rule(m):
        return sum(m.x[p, a] for p in m.PEAKS for a in m.AMINO_ACIDS) == num_assignments

    model.total_assignments = pyo.Constraint(rule=total_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}