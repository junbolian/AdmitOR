import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arcs = params["arcs"]
    arc_capacity = params["arc_capacity"]
    commodity_demand = params["commodity_demand"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    nodes = list(range(num_nodes))
    commodities = list(range(num_commodities))
    arc_list = [tuple(a) for a in arcs]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes, ordered=True)
    model.COMMODITIES = pyo.Set(initialize=commodities, ordered=True)
    model.ARCS = pyo.Set(initialize=arc_list, dimen=2, ordered=True)

    model.flow = pyo.Var(model.ARCS, model.COMMODITIES, domain=pyo.NonNegativeReals)

    model.util = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(m, i, j):
        return sum(m.flow[i, j, k] for k in m.COMMODITIES) <= arc_capacity[arc_list.index((i, j))] * m.util

    model.capacity_con = pyo.Constraint(model.ARCS, rule=capacity_rule)

    def flow_conservation_rule(m, i, k):
        outflow = sum(m.flow[i, j, k] for (a, j) in arc_list if a == i)
        inflow = sum(m.flow[j, i, k] for (j, a) in arc_list if a == i)
        rhs = 0
        if i == commodity_source[k]:
            rhs += commodity_demand[k]
        if i == commodity_sink[k]:
            rhs -= commodity_demand[k]
        return outflow - inflow == rhs

    model.balance_con = pyo.Constraint(model.NODES, model.COMMODITIES, rule=flow_conservation_rule)

    model.obj = pyo.Objective(expr=model.util, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}