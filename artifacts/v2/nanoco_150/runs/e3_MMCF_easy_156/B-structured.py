# IR: {"sets":{"N":"0..9","E":[[0,1],[0,4],[1,2],[1,5],[2,3],[2,6],[3,4],[3,9],[4,5],[4,6],[5,6],[5,7],[6,7],[7,8],[8,9]],"A":"For each (i,j) in E, append (i,j), then (j,i), preserving E order","K":[1,2]},"params":{"capacities":"Nonnegative array indexed in A order, read from params['capacities']","unit_costs":"Real-valued network attribute array indexed in A order, read from params['unit_costs']; excluded from objective","demands":"Nonnegative array in K order, read from params['demands']","sources":{"1":1,"2":0},"sinks":{"1":7,"2":4}},"variables":{"flow[k,i,j]":"Nonnegative continuous for k in K and (i,j) in A","peak_congestion":"Nonnegative continuous"},"constraints":["For each k,n: outgoing flow minus incoming flow equals demands[k] at sources[k], -demands[k] at sinks[k], and 0 otherwise","For each (i,j): sum_k flow[k,i,j] <= capacities[i,j]","For each (i,j): sum_k flow[k,i,j] <= capacities[i,j] * peak_congestion; zero-capacity arcs must carry zero flow"],"objective":"Minimize peak_congestion"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1), (0, 4), (1, 2), (1, 5), (2, 3),
        (2, 6), (3, 4), (3, 9), (4, 5), (4, 6),
        (5, 6), (5, 7), (6, 7), (7, 8), (8, 9),
    ]
    arcs = [
        directed_arc
        for i, j in edges
        for directed_arc in ((i, j), (j, i))
    ]
    commodities = (1, 2)
    sources = {1: 1, 2: 0}
    sinks = {1: 7, 2: 4}

    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    demands = params["demands"]

    if len(capacities) != len(arcs):
        raise ValueError("capacities must contain exactly 30 entries.")
    if len(unit_costs) != len(arcs):
        raise ValueError("unit_costs must contain exactly 30 entries.")
    if len(demands) != len(commodities):
        raise ValueError("demands must contain exactly 2 entries.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.commodities = pyo.Set(initialize=commodities, ordered=True)

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacities[idx] for idx, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )
    model.arc_unit_cost = pyo.Param(
        model.arcs,
        initialize={arc: unit_costs[idx] for idx, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.commodity_demand = pyo.Param(
        model.commodities,
        initialize={k: demands[idx] for idx, k in enumerate(commodities)},
        within=pyo.NonNegativeReals,
    )
    model.commodity_source = pyo.Param(
        model.commodities, initialize=sources, within=model.nodes
    )
    model.commodity_sink = pyo.Param(
        model.commodities, initialize=sinks, within=model.nodes
    )

    model.flow = pyo.Var(
        model.commodities, model.arcs, domain=pyo.NonNegativeReals
    )
    model.peak_congestion = pyo.Var(domain=pyo.NonNegativeReals)

    outgoing = {
        node: [arc for arc in arcs if arc[0] == node]
        for node in range(10)
    }
    incoming = {
        node: [arc for arc in arcs if arc[1] == node]
        for node in range(10)
    }

    def flow_balance_rule(network, k, node):
        net_outflow = (
            sum(network.flow[k, i, j] for i, j in outgoing[node])
            - sum(network.flow[k, i, j] for i, j in incoming[node])
        )
        if node == pyo.value(network.commodity_source[k]):
            return net_outflow == network.commodity_demand[k]
        if node == pyo.value(network.commodity_sink[k]):
            return net_outflow == -network.commodity_demand[k]
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.commodities, model.nodes, rule=flow_balance_rule
    )

    def capacity_rule(network, i, j):
        return (
            sum(network.flow[k, i, j] for k in network.commodities)
            <= network.arc_capacity[i, j]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def congestion_rule(network, i, j):
        return (
            sum(network.flow[k, i, j] for k in network.commodities)
            <= network.arc_capacity[i, j] * network.peak_congestion
        )

    model.congestion_limits = pyo.Constraint(
        model.arcs, rule=congestion_rule
    )
    model.congestion_objective = pyo.Objective(
        expr=model.peak_congestion, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.congestion_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}