import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["shipment_weights"]
    cap = params["truck_capacity"]
    n = len(weights)
    T = n  # at most n trucks needed

    model = pyo.ConcreteModel()
    model.S = pyo.RangeSet(0, n - 1)
    model.T = pyo.RangeSet(0, T - 1)

    model.x = pyo.Var(model.S, model.T, domain=pyo.Binary)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    def assign_rule(m, i):
        return sum(m.x[i, t] for t in m.T) == 1

    model.assign_con = pyo.Constraint(model.S, rule=assign_rule)

    def cap_rule(m, t):
        return sum(weights[i] * m.x[i, t] for i in m.S) <= cap * m.y[t]

    model.cap_con = pyo.Constraint(model.T, rule=cap_rule)

    def sym_rule(m, t):
        if t < T - 1:
            return m.y[t] >= m.y[t + 1]
        return pyo.Constraint.Skip

    model.sym_con = pyo.Constraint(model.T, rule=sym_rule)

    model.obj = pyo.Objective(expr=sum(model.y[t] for t in model.T), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}