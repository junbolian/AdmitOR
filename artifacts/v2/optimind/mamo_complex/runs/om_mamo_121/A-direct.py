import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_food = params["initial_food"]
    required_food = params["required_food"]
    transport_cost = params["transport_cost"]

    regions = list(range(6))

    model = pyo.ConcreteModel()

    model.R = pyo.Set(initialize=regions)
    model.RR = pyo.Set(initialize=[(i, j) for i in regions for j in regions if i != j])

    model.x = pyo.Var(model.RR, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j] for (i, j) in m.RR)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return initial_food[i] + sum(m.x[j, i] for (j, k) in m.RR if k == i) >= required_food[i]

    model.supply = pyo.Constraint(model.R, rule=supply_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}