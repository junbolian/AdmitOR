import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost_matrix"]
    n = len(cost)

    model = pyo.ConcreteModel()
    model.A = pyo.RangeSet(0, n - 1)
    model.I = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.A, model.I, domain=pyo.Binary)
    model.T = pyo.Var(domain=pyo.NonNegativeReals)

    model.assign_analyst = pyo.Constraint(
        model.A, rule=lambda m, a: sum(m.x[a, i] for i in m.I) == 1
    )
    model.assign_incident = pyo.Constraint(
        model.I, rule=lambda m, i: sum(m.x[a, i] for a in m.A) == 1
    )
    model.bottleneck = pyo.Constraint(
        model.A,
        model.I,
        rule=lambda m, a, i: cost[a][i] * m.x[a, i] <= m.T,
    )

    model.obj = pyo.Objective(expr=model.T, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}