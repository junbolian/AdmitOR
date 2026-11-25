# IR: {"sets":{"N":"range(params['num_nodes'])","K":"range(params['num_commodities'])","E":[[0,1],[0,3],[0,5],[0,6],[0,7],[1,2],[1,5],[1,6],[2,3],[2,6],[3,4],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]],"A":"for each (u,v) in E, append (u,v), then (v,u)"},"params":{"num_nodes":"params['num_nodes']; frozen at 8","num_commodities":"params['num_commodities']; frozen at 2","capacity[a]":"params['arc_capacities'][position(a)]","cost[a]":"params['arc_unit_costs'][position(a)]","demand[k]":"params['demands'][k]","source":"[3,1]","sink":"[7,5]"},"variables":{"flow[k,u,v]":"nonnegative continuous, k in K, (u,v) in A"},"constraints":["For each k,n: sum(flow[k,n,v]) - sum(flow[k,u,n]) = demand[k] if n=source[k], -demand[k] if n=sink[k], otherwise 0.","For each (u,v): sum_k flow[k,u,v] <= capacity[u,v]."],"objective":"minimize sum_{k,(u,v)} cost[u,v] * flow[k,u,v]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]

    if num_nodes != 8 or num_commodities != 2:
        return {"objective": None, "status": "invalid_dimensions"}

    undirected_edges = [
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 5), (1, 6),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    arcs = [
        directed_arc
        for origin, destination in undirected_edges
        for directed_arc in (
            (origin, destination),
            (destination, origin),
        )
    ]

    if (
        len(arc_capacities) != len(arcs)
        or len(arc_unit_costs) != len(arcs)
        or len(demands) != num_commodities
    ):
        return {"objective": None, "status": "invalid_parameter_lengths"}

    sources = (3, 1)
    sinks = (7, 5)
    node_indices = range(num_nodes)
    commodity_indices = range(num_commodities)

    outgoing = {
        node: [destination for origin, destination in arcs if origin == node]
        for node in node_indices
    }
    incoming = {
        node: [origin for origin, destination in arcs if destination == node]
        for node in node_indices
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=node_indices, ordered=True)
    model.commodity_ids = pyo.Set(initialize=commodity_indices, ordered=True)
    model.directed_arcs = pyo.Set(
        initialize=arcs, dimen=2, ordered=True
    )

    model.arc_capacity = pyo.Param(
        model.directed_arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.directed_arcs,
        initialize={
            arc: arc_unit_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.delivery_demand = pyo.Param(
        model.commodity_ids,
        initialize={
            commodity: demands[commodity]
            for commodity in commodity_indices
        },
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(
        model.commodity_ids,
        model.directed_arcs,
        domain=pyo.NonNegativeReals,
    )

    def balance_rule(grid, commodity, node):
        net_outflow = (
            pyo.quicksum(
                grid.flow[commodity, node, destination]
                for destination in outgoing[node]
            )
            - pyo.quicksum(
                grid.flow[commodity, origin, node]
                for origin in incoming[node]
            )
        )
        if node == sources[commodity]:
            return net_outflow == grid.delivery_demand[commodity]
        if node == sinks[commodity]:
            return net_outflow == -grid.delivery_demand[commodity]
        return net_outflow == 0

    model.power_balance = pyo.Constraint(
        model.commodity_ids,
        model.nodes,
        rule=balance_rule,
    )

    def capacity_rule(grid, origin, destination):
        return (
            pyo.quicksum(
                grid.flow[commodity, origin, destination]
                for commodity in grid.commodity_ids
            )
            <= grid.arc_capacity[origin, destination]
        )

    model.thermal_limit = pyo.Constraint(
        model.directed_arcs,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.arc_cost[origin, destination]
            * model.flow[commodity, origin, destination]
            for commodity in model.commodity_ids
            for origin, destination in model.directed_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}