import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    peaks = list(range(5))
    aas = list(range(6))

    cost = {}
    for p in peaks:
        for a in aas:
            cost[(p, a)] = params[f"cost_peak{p}_aa{a}"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=peaks)
    model.A = pyo.Set(initialize=aas)
    model.PA = pyo.Set(initialize=[(p, a) for p in peaks for a in aas], dimen=2)

    model.x = pyo.Var(model.PA, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(p, a)] * m.x[(p, a)] for p in m.P for a in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_rule(m, p):
        return sum(m.x[(p, a)] for a in m.A) <= 1

    model.peak_con = pyo.Constraint(model.P, rule=peak_rule)

    def aa_rule(m, a):
        return sum(m.x[(p, a)] for p in m.P) <= 1

    model.aa_con = pyo.Constraint(model.A, rule=aa_rule)

    def total_rule(m):
        return sum(m.x[(p, a)] for p in m.P for a in m.A) == params["num_assignments_required"]

    model.total_con = pyo.Constraint(rule=total_rule)

    def noe1_rule(m):
        return m.x[(1, 1)] + m.x[(2, 0)] <= params["noe_pair_p1aa1_p2aa0_rhs"]

    model.noe1_con = pyo.Constraint(rule=noe1_rule)

    def noe2_rule(m):
        return m.x[(1, 3)] + m.x[(2, 0)] <= params["noe_pair_p1aa3_p2aa0_rhs"]

    model.noe2_con = pyo.Constraint(rule=noe2_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}