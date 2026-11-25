import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_prod = 3
    n_contract = 4

    capacity = [params["capacity_0"], params["capacity_1"], params["capacity_2"]]
    demand = [params["demand_0"], params["demand_1"], params["demand_2"], params["demand_3"]]
    min_del = [params["min_delivery_0"], params["min_delivery_1"], params["min_delivery_2"]]
    cost = [
        [params["cost_0_0"], params["cost_0_1"], params["cost_0_2"], params["cost_0_3"]],
        [params["cost_1_0"], params["cost_1_1"], params["cost_1_2"], params["cost_1_3"]],
        [params["cost_2_0"], params["cost_2_1"], params["cost_2_2"], params["cost_2_3"]],
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_prod - 1)
    model.C = pyo.RangeSet(0, n_contract - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.capacity_con = pyo.Constraint(
        model.P,
        rule=lambda m, p: sum(m.x[p, c] for c in m.C) <= capacity[p]
    )

    model.demand_con = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(m.x[p, c] for p in m.P) >= demand[c]
    )

    model.min_contrib_con = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(m.y[p, c] for p in m.P) >= 2
    )

    def min_delivery_rule(m, p, c):
        return m.x[p, c] >= min_del[p] * m.y[p, c]

    model.min_delivery_con = pyo.Constraint(model.P, model.C, rule=min_delivery_rule)

    def linking_rule(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]

    model.linking_con = pyo.Constraint(model.P, model.C, rule=linking_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}