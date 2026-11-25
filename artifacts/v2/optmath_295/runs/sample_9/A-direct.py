import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (3, 0), (0, 4), (4, 0),
        (0, 5), (5, 0), (0, 6), (6, 0), (1, 2), (2, 1), (1, 3), (3, 1),
        (1, 4), (4, 1), (1, 5), (5, 1), (1, 6), (6, 1), (2, 3), (3, 2),
        (2, 4), (4, 2), (2, 5), (5, 2), (2, 6), (6, 2), (3, 4), (4, 3),
        (3, 5), (5, 3), (3, 6), (6, 3), (4, 5), (5, 4), (4, 6), (6, 4),
        (5, 6), (6, 5),
    ]
    nodes = [0, 1, 2, 3, 4, 5, 6]

    fixed_cost = params["fixed_cost_matrix"]
    var_cost = params["variable_cost_matrix"]
    cap = params["capacity_matrix"]

    fixed_map = {a: fixed_cost[k] for k, a in enumerate(arcs)}
    var_map = {a: var_cost[k] for k, a in enumerate(arcs)}
    cap_map = {a: cap[k] for k, a in enumerate(arcs)}

    net = {
        0: params["supply_node0"],
        1: params["supply_node1"],
        2: 0.0,
        3: 0.0,
        4: 0.0,
        5: -params["demand_node5"],
        6: -params["demand_node6"],
    }

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.NODE = pyo.Set(initialize=nodes)

    model.y = pyo.Var(model.ARC, domain=pyo.Binary)
    model.x = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    def flow_limit_rule(mdl, i, j):
        return mdl.x[i, j] <= cap_map[(i, j)] * mdl.y[i, j]

    model.flow_limit = pyo.Constraint(model.ARC, rule=flow_limit_rule)

    def balance_rule(mdl, n):
        out_flow = sum(mdl.x[n, j] for j in nodes if (n, j) in fixed_map)
        in_flow = sum(mdl.x[i, n] for i in nodes if (i, n) in fixed_map)
        return out_flow - in_flow == net[n]

    model.balance = pyo.Constraint(model.NODE, rule=balance_rule)

    def obj_rule(mdl):
        return sum(fixed_map[a] * mdl.y[a] for a in arcs) + sum(
            var_map[a] * mdl.x[a] for a in arcs
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}