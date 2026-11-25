import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    node_coordinates = params["node_coordinates"]
    num_edges = params["num_edges"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    commodity_supply = params["commodity_supply"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    edges = [
        (0, 1), (0, 3), (0, 5), (1, 2), (1, 7), (2, 3), (2, 6), (2, 7),
        (3, 4), (4, 5), (4, 6), (5, 6), (6, 7), (7, 8),
    ]
    arcs = []
    for (u, v) in edges:
        arcs.append((u, v))
        arcs.append((v, u))

    arc_cap = {arcs[i]: arc_capacities[i] for i in range(len(arcs))}
    arc_cost = {arcs[i]: arc_unit_costs[i] for i in range(len(arcs))}

    commodities = list(range(num_commodities))
    nodes = list(range(num_nodes))

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.COMMODITIES = pyo.Set(initialize=commodities)

    model.flow = pyo.Var(model.COMMODITIES, model.ARCS, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    def arc_utilization_rule(model, u, v):
        total = sum(model.flow[k, u, v] for k in model.COMMODITIES)
        return total <= arc_cap[(u, v)] * model.z

    model.arc_utilization = pyo.Constraint(model.ARCS, rule=arc_utilization_rule)

    def flow_conservation_rule(model, k, i):
        outflow = sum(model.flow[k, i, j] for (i2, j) in arcs if i2 == i)
        inflow = sum(model.flow[k, j, i] for (j, i2) in arcs if i2 == i)
        if i == commodity_source[k]:
            return outflow - inflow == commodity_supply[k]
        elif i == commodity_sink[k]:
            return outflow - inflow == -commodity_supply[k]
        else:
            return outflow - inflow == 0

    model.flow_conservation = pyo.Constraint(
        model.COMMODITIES * model.NODES, rule=flow_conservation_rule
    )

    model.objective = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}