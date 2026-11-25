import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_peaks = int(params["num_peaks"])
    num_aa = int(params["num_amino_acids"])
    peaks = list(range(num_peaks))
    aas = list(range(num_aa))

    cost = {}
    for p in peaks:
        for a in aas:
            cost[(p, a)] = params[f"cost_peak{p}_aa{a}"]

    num_assignments = int(params["num_assignments"])

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.Set(initialize=peaks)
    model.AAS = pyo.Set(initialize=aas)

    model.x = pyo.Var(model.PEAKS, model.AAS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(p, a)] * m.x[p, a] for p in m.PEAKS for a in m.AAS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_limit_rule(m, p):
        return sum(m.x[p, a] for a in m.AAS) <= 1

    model.peak_limit = pyo.Constraint(model.PEAKS, rule=peak_limit_rule)

    def aa_limit_rule(m, a):
        return sum(m.x[p, a] for p in m.PEAKS) <= 1

    model.aa_limit = pyo.Constraint(model.AAS, rule=aa_limit_rule)

    def num_assign_rule(m):
        return sum(m.x[p, a] for p in m.PEAKS for a in m.AAS) == num_assignments

    model.num_assign = pyo.Constraint(rule=num_assign_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}