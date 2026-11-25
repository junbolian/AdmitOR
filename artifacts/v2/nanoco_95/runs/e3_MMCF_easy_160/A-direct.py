import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = 9
    num_commodities = 2
    edges = [
        (0, 1), (0, 3), (0, 5), (1, 2), (1, 7), (2, 3),
        (2, 6), (2, 7), (3, 4), (4, 5), (4, 6), (5, 6), (6, 7), (7, 8),
    ]
    arcs = []
    for (u, v) in edges:
        arcs.append((u, v))
        arcs.append((v, u))

    capacities = list(params["arc_capacities"])
    unit_costs = list(params["arc_unit_costs"])
    supplies = list(params["commodity_supplies"])
    coords_x = list(params["node_coordinates_x"])
    coords_y = list(params["node_coordinates_y"])

    # commodity source/sink structure: commodity 1 (index 0) src 3 -> sink 2
    # commodity 2 (index 1) src 6 -> sink 1
    src = [3, 6]
    snk = [2, 1]

    arc_index = list(range(len(arcs)))
    comm_index = list(range(num_commodities))
    node_index = list(range(num_nodes))

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arc_index, ordered=True)
    model.COMM = pyo.Set(initialize=comm_index, ordered=True)
    model.NODES = pyo.Set(initialize=node_index, ordered=True)

    def arc_tail(i):
        return arcs[i][0]

    def arc_head(i):
        return arcs[i][1]

    def capacity_rule(model, i):
        return float(capacities[i])

    model.arc_cap = pyo.Param(model.ARCS, initialize=capacity_rule, within=pyo.NonNegativeReals)

    model.flow = pyo.Var(model.COMM, model.ARCS, domain=pyo.NonNegativeReals)
    model.util = pyo.Var(domain=pyo.NonNegativeReals)

    # capacity / utilization linking constraints
    def util_rule(model, i):
        return sum(model.flow[k, i] for k in model.COMM) <= model.util * model.arc_cap[i]

    model.util_con = pyo.Constraint(model.ARCS, rule=util_rule)

    # flow conservation
    def balance_rule(model, k, n):
        inflow = sum(model.flow[k, i] for i in model.ARCS if arc_head(i) == n)
        outflow = sum(model.flow[k, i] for i in model.ARCS if arc_tail(i) == n)
        if n == src[k]:
            return outflow - inflow == float(supplies[k])
        elif n == snk[k]:
            return inflow - outflow == float(supplies[k])
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(model.COMM, model.NODES, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.util, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}