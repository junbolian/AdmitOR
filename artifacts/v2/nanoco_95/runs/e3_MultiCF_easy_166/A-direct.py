import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_arcs = int(params["num_arcs"])
    num_commodities = int(params["num_commodities"])

    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    commodity_demand = params["commodity_demand"]

    nodes = list(range(num_nodes))
    arcs = list(range(num_arcs))
    commodities = list(range(num_commodities))

    undirected_edges = [
        [0, 1], [0, 4], [1, 2], [1, 5], [2, 3], [2, 6], [3, 4], [3, 9],
        [4, 5], [4, 6], [5, 6], [5, 7], [6, 7], [7, 8], [8, 9]
    ]
    arc_list = []
    for u, v in undirected_edges:
        arc_list.append((u, v))
        arc_list.append((v, u))

    sources = [1, 0]
    sinks = [7, 4]

    arcs_out = {n: [a for a in arcs if arc_list[a][0] == n] for n in nodes}
    arcs_in = {n: [a for a in arcs if arc_list[a][1] == n] for n in nodes}

    model = pyo.ConcreteModel()

    model.node_set = pyo.Set(initialize=nodes)
    model.arc_set = pyo.Set(initialize=arcs)
    model.commodity_set = pyo.Set(initialize=commodities)

    model.capacity = pyo.Param(model.arc_set,
                               initialize={a: arc_capacity[a] for a in arcs})
    model.cost = pyo.Param(model.arc_set,
                           initialize={a: arc_cost[a] for a in arcs})
    model.demand = pyo.Param(model.commodity_set,
                             initialize={k: commodity_demand[k] for k in commodities})

    model.flow = pyo.Var(model.commodity_set, model.arc_set,
                         domain=pyo.NonNegativeReals)

    def flow_balance_rule(model, k, n):
        outflow = sum(model.flow[k, a] for a in arcs_out[n])
        inflow = sum(model.flow[k, a] for a in arcs_in[n])
        if n == sources[k]:
            return outflow - inflow == model.demand[k]
        elif n == sinks[k]:
            return inflow - outflow == model.demand[k]
        else:
            return inflow - outflow == 0

    model.flow_balance = pyo.Constraint(model.commodity_set, model.node_set,
                                        rule=flow_balance_rule)

    def capacity_rule(model, a):
        return sum(model.flow[k, a] for k in commodities) <= model.capacity[a]

    model.capacity_limit = pyo.Constraint(model.arc_set, rule=capacity_rule)

    def objective_rule(model):
        return sum(model.cost[a] * model.flow[k, a]
                   for k in commodities for a in arcs)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}