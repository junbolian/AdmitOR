# IR: {"sets":{"N":"range(params['num_nodes'])","K":"range(params['num_commodities'])","E":[[0,1],[0,3],[0,5],[0,6],[0,7],[1,2],[1,5],[1,6],[2,3],[2,6],[3,4],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]],"A":"each edge (i,j) in E expanded consecutively as (i,j),(j,i)"},"params":{"arc_capacities":"params['arc_capacities'], indexed by A order, nonnegative","arc_unit_costs":"params['arc_unit_costs'], indexed by A order, real","demands":"params['demands'], indexed by K, nonnegative","num_nodes":"params['num_nodes'], frozen at 8","num_commodities":"params['num_commodities'], frozen at 2","sources":[3,1],"sinks":[7,5]},"decision_variables":{"flow[k,i,j]":"nonnegative continuous, k in K, (i,j) in A"},"constraints":["For each k,n: sum_j flow[k,n,j] - sum_i flow[k,i,n] = demands[k] * (1[n=sources[k]] - 1[n=sinks[k]]).","For each (i,j): sum_k flow[k,i,j] <= arc_capacities[i,j]."],"objective":"Minimize sum_{k,(i,j)} arc_unit_costs[i,j] * flow[k,i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]

    # Network dimensions and commodity endpoints are frozen structure.
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
        for node_i, node_j in undirected_edges
        for directed_arc in ((node_i, node_j), (node_j, node_i))
    ]
    sources = (3, 1)
    sinks = (7, 5)

    if (
        len(arc_capacities) != len(arcs)
        or len(arc_unit_costs) != len(arcs)
        or len(demands) != num_commodities
    ):
        return {"objective": None, "status": "invalid_parameter_lengths"}

    outgoing = {
        node: [node_j for node_i, node_j in arcs if node_i == node]
        for node in range(num_nodes)
    }
    incoming = {
        node: [node_i for node_i, node_j in arcs if node_j == node]
        for node in range(num_nodes)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.commodities = pyo.Set(
        initialize=range(num_commodities), ordered=True
    )
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_unit_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.commodities,
        initialize={
            commodity: demands[commodity]
            for commodity in range(num_commodities)
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.commodities, model.arcs, domain=pyo.NonNegativeReals
    )

    def balance_rule(grid, commodity, node):
        net_outflow = (
            sum(
                grid.flow[commodity, node, destination]
                for destination in outgoing[node]
            )
            - sum(
                grid.flow[commodity, origin, node]
                for origin in incoming[node]
            )
        )
        required_net_outflow = grid.demand[commodity] * (
            int(node == sources[commodity])
            - int(node == sinks[commodity])
        )
        return net_outflow == required_net_outflow

    model.flow_balance = pyo.Constraint(
        model.commodities, model.nodes, rule=balance_rule
    )

    def capacity_rule(grid, node_i, node_j):
        return (
            sum(
                grid.flow[commodity, node_i, node_j]
                for commodity in grid.commodities
            )
            <= grid.capacity[node_i, node_j]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[node_i, node_j]
            * model.flow[commodity, node_i, node_j]
            for commodity in model.commodities
            for node_i, node_j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution is available to load.
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}