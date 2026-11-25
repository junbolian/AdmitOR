import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    peaks = list(range(4))
    aminos = list(range(5))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=peaks)
    model.A = pyo.Set(initialize=aminos)

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[p][a] * model.x[p, a] for p in model.P for a in model.A),
        sense=pyo.minimize,
    )

    # Each peak assigned to at most one amino acid
    def peak_rule(m, p):
        return sum(m.x[p, a] for a in m.A) <= 1

    model.peak_con = pyo.Constraint(model.P, rule=peak_rule)

    # Each amino acid assigned to at most one peak
    def amino_rule(m, a):
        return sum(m.x[p, a] for p in m.P) <= 1

    model.amino_con = pyo.Constraint(model.A, rule=amino_rule)

    # Exactly 3 assignments
    def total_rule(m):
        return sum(m.x[p, a] for p in m.P for a in m.A) == 3

    model.total_con = pyo.Constraint(rule=total_rule)

    # Restricted pairs
    def r1_rule(m):
        return m.x[0, 1] + m.x[2, 4] <= 1

    model.r1 = pyo.Constraint(rule=r1_rule)

    def r2_rule(m):
        return m.x[1, 1] + m.x[2, 4] <= 1

    model.r2 = pyo.Constraint(rule=r2_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}