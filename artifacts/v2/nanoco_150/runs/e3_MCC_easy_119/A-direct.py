import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    coords = params["coordinates"]
    route_cost = params["route_cost"]
    route_min = params["route_min_flow"]
    route_max = params["route_max_capacity"]

    routes = list(range(17))
    nodes = list(range(6))

    # arc list: (from, to) in the given order
    arcs = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 1), (2, 3),
        (3, 1), (3, 2), (3, 4),
        (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 2), (5, 3), (5, 4),
    ]

    # index maps
    out_arcs = {i: [] for i in nodes}
    in_arcs = {i: [] for i in nodes}
    for k, (a, b) in enumerate(arcs):
        out_arcs[a].append(k)
        in_arcs[b].append(k)

    model = pyo.ConcreteModel()

    model.R = pyo.RangeSet(0, len(arcs) - 1)
    model.N = pyo.RangeSet(0, len(nodes) - 1)

    model.f = pyo.Var(model.R, domain=pyo.NonNegativeReals,
                      bounds=lambda m, k: (route_min[k], route_max[k]))

    def flow_balance_rule(m, i):
        return sum(m.f[k] for k in out_arcs[i]) == sum(m.f[k] for k in in_arcs[i])
    model.flow_balance = pyo.Constraint(model.N, rule=flow_balance_rule)

    def obj_rule(m):
        return sum(route_cost[k] * m.f[k] for k in m.R)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}