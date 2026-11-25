import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = 8
    undirected_edges = [
        [0, 1], [0, 3], [0, 5], [0, 6], [0, 7], [1, 2], [1, 5], [1, 6],
        [2, 3], [2, 6], [3, 4], [4, 5], [4, 6], [4, 7], [5, 6], [5, 7], [6, 7]
    ]
    arcs = []
    for u, v in undirected_edges:
        arcs.append((u, v))
        arcs.append((v, u))

    commodities = [
        {"source": 3, "sink": 7, "demand": params["demands"][0]},
        {"source": 1, "sink": 5, "demand": params["demands"][1]},
    ]

    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    nodes = list(range(num_nodes))
    arc_indices = list(range(len(arcs)))
    comm_indices = list(range(len(commodities)))

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arc_indices)
    model.K = pyo.Set(initialize=comm_indices)

    model.flow = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(arc_unit_costs[a] * mdl.flow[k, a] for k in mdl.K for a in mdl.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(mdl, k, n):
        src = commodities[k]["source"]
        snk = commodities[k]["sink"]
        if n == src:
            return sum(mdl.flow[k, a] for a in mdl.A if arcs[a][0] == n) - \
                   sum(mdl.flow[k, a] for a in mdl.A if arcs[a][1] == n) == commodities[k]["demand"]
        elif n == snk:
            return sum(mdl.flow[k, a] for a in mdl.A if arcs[a][1] == n) - \
                   sum(mdl.flow[k, a] for a in mdl.A if arcs[a][0] == n) == commodities[k]["demand"]
        else:
            return sum(mdl.flow[k, a] for a in mdl.A if arcs[a][0] == n) - \
                   sum(mdl.flow[k, a] for a in mdl.A if arcs[a][1] == n) == 0

    model.balance = pyo.Constraint(model.K, model.N, rule=balance_rule)

    def cap_rule(mdl, a):
        return sum(mdl.flow[k, a] for k in mdl.K) <= arc_capacities[a]

    model.cap = pyo.Constraint(model.A, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}