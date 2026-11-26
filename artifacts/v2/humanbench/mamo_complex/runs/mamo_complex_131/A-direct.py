import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n - 1)
    model.J = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            transport_cost[i][j] * m.x[i, j]
            for i in m.I
            for j in m.J
            if i != j
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J if j != i) - sum(
            m.x[j, i] for j in m.J if j != i
        ) == demand[i] - supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    for i in model.I:
        for j in model.J:
            if i == j:
                model.x[i, j].fix(0)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}