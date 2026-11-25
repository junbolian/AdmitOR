import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    demands = params["demands"]
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]

    arcs = [(0, 1), (1, 0), (0, 3), (3, 0), (0, 5), (5, 0), (0, 6), (6, 0),
            (0, 7), (7, 0), (1, 2), (2, 1), (1, 5), (5, 1), (1, 6), (6, 1),
            (2, 3), (3, 2), (2, 6), (6, 2), (3, 4), (4, 3), (4, 5), (5, 4),
            (4, 6), (6, 4), (4, 7), (7, 4), (5, 6), (6, 5), (5, 7), (7, 5),
            (6, 7), (7, 6)]

    comm_src = {1: 3, 2: 1}
    comm_sink = {1: 7, 2: 5}
    comm_demand = {1: demands[0], 2: demands[1]}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.COMM = pyo.Set(initialize=[1, 2])
    model.NODES = pyo.Set(initialize=list(range(num_nodes)))

    cap_map = {arcs[i]: capacities[i] for i in range(len(arcs))}

    model.flow = pyo.Var(model.COMM, model.ARCS, domain=pyo.NonNegativeReals)
    model.util = pyo.Var(domain=pyo.NonNegativeReals)

    def util_rule(m, a):
        return sum(m.flow[k, a] for k in m.COMM) <= m.util * cap_map[a]
    model.util_con = pyo.Constraint(model.ARCS, rule=util_rule)

    def balance_rule(m, k, n):
        inflow = sum(m.flow[k, (i, j)] for (i, j) in arcs if j == n)
        outflow = sum(m.flow[k, (i, j)] for (i, j) in arcs if i == n)
        if n == comm_src[k]:
            return outflow - inflow == comm_demand[k]
        elif n == comm_sink[k]:
            return inflow - outflow == comm_demand[k]
        else:
            return inflow - outflow == 0
    model.balance = pyo.Constraint(model.COMM, model.NODES, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.util, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}