import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    num_assignments = params["num_assignments"]
    num_peaks = params["num_peaks"]
    num_amino_acids = params["num_amino_acids"]

    model = pyo.ConcreteModel()

    model.peaks = pyo.RangeSet(0, num_peaks - 1)
    model.amino_acids = pyo.RangeSet(0, num_amino_acids - 1)

    model.assign = pyo.Var(model.peaks, model.amino_acids, domain=pyo.Binary)

    def objective_rule(m):
        return sum(cost[i][j] * m.assign[i, j]
                   for i in m.peaks for j in m.amino_acids)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def peak_rule(m, i):
        return sum(m.assign[i, j] for j in m.amino_acids) <= 1

    model.peak_constraint = pyo.Constraint(model.peaks, rule=peak_rule)

    def aa_rule(m, j):
        return sum(m.assign[i, j] for i in m.peaks) <= 1

    model.aa_constraint = pyo.Constraint(model.amino_acids, rule=aa_rule)

    def total_rule(m):
        return sum(m.assign[i, j]
                   for i in m.peaks for j in m.amino_acids) == num_assignments

    model.total_constraint = pyo.Constraint(rule=total_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}