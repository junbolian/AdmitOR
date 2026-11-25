import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 2), (1, 3),
    ]
    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (0, 4): params["cost_0_4"],
        (0, 5): params["cost_0_5"],
        (0, 6): params["cost_0_6"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
    }

    supply = {0: params["node_0_supply"]}
    demand = {6: params["node_6_demand"]}

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARC, within=pyo.Binary)

    def obj_rule(m):
        return sum(cost[a] * m.x[a] for a in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, n):
        out_flow = sum(m.x[a] for a in arcs if a[0] == n)
        in_flow = sum(m.x[a] for a in arcs if a[1] == n)
        if n == 0:
            return out_flow - in_flow == supply[0]
        if n == 6:
            return in_flow - out_flow == demand[6]
        return out_flow - in_flow == 0
    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}