import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    demands = params["demands"]

    undirected = [
        (0, 1), (0, 4), (1, 2), (1, 5), (2, 3), (2, 6), (3, 4), (3, 9),
        (4, 5), (4, 6), (5, 6), (5, 7), (6, 7), (7, 8), (8, 9),
    ]
    arcs = []
    for (u, v) in undirected:
        arcs.append((u, v))
        arcs.append((v, u))

    num_arcs = len(arcs)

    nodes = list(range(10))
    # commodity index 0 -> node 1 to 7 ; commodity index 1 -> node 0 to 4
    commodities = [0, 1]
    origin = {0: 1, 1: 0}
    dest = {0: 7, 1: 4}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.RangeSet(0, num_arcs - 1)
    model.NODES = pyo.Set(initialize=nodes)
    model.COMMODITIES = pyo.Set(initialize=commodities)

    cap = {a: capacities[a] for a in range(num_arcs)}

    model.x = pyo.Var(model.COMMODITIES, model.ARCS, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    # Capacity constraint
    def capacity_rule(m, a):
        return sum(m.x[k, a] for k in m.COMMODITIES) <= cap[a]
    model.capacity_con = pyo.Constraint(model.ARCS, rule=capacity_rule)

    # Flow conservation
    def flow_balance_rule(m, k, n):
        outflow = sum(m.x[k, a] for a in m.ARCS if arcs[a][0] == n)
        inflow = sum(m.x[k, a] for a in m.ARCS if arcs[a][1] == n)
        net = demands[k] if n == origin[k] else (-demands[k] if n == dest[k] else 0)
        return outflow - inflow == net
    model.flow_balance = pyo.Constraint(model.COMMODITIES, model.NODES,
                                        rule=flow_balance_rule)

    # Congestion index constraint
    def congestion_rule(m, a):
        return sum(m.x[k, a] for k in m.COMMODITIES) <= m.z * cap[a]
    model.congestion_con = pyo.Constraint(model.ARCS, rule=congestion_rule)

    model.OBJ = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.OBJ))
    return {"objective": obj_val, "status": "optimal"}