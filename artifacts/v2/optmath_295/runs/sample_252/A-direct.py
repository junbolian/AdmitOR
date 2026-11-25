import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    peak_count = params["peak_count"]
    amino_acid_count = params["amino_acid_count"]
    required_assignments = params["required_assignments"]
    cost_matrix = params["cost_matrix"]
    noe_pairs = params["noe_pairs"]

    peaks = range(peak_count)
    aminos = range(amino_acid_count)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peaks, aminos, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for i in peaks for j in aminos)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(m, i):
        return sum(m.x[i, j] for j in aminos) <= 1

    model.peak_con = pyo.Constraint(peaks, rule=peak_rule)

    def amino_rule(m, j):
        return sum(m.x[i, j] for i in peaks) <= 1

    model.amino_con = pyo.Constraint(aminos, rule=amino_rule)

    def total_rule(m):
        return sum(m.x[i, j] for i in peaks for j in aminos) == required_assignments

    model.total_con = pyo.Constraint(rule=total_rule)

    def noe_rule(m, k):
        pa, aa, pb, ab = noe_pairs[k]
        return m.x[pa, aa] + m.x[pb, ab] <= 1

    model.noe_con = pyo.Constraint(range(len(noe_pairs)), rule=noe_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}