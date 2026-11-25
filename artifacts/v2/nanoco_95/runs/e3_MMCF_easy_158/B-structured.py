# IR: {"sets":{"N":"range(params['num_nodes']); size 8","K":"range(params['num_commodities']); size 2","A":[[0,1],[1,0],[0,3],[3,0],[0,5],[5,0],[0,6],[6,0],[0,7],[7,0],[1,2],[2,1],[1,5],[5,1],[1,6],[6,1],[2,3],[3,2],[2,6],[6,2],[3,4],[4,3],[4,5],[5,4],[4,6],[6,4],[4,7],[7,4],[5,6],[6,5],[5,7],[7,5],[6,7],[7,6]]},"params":{"capacity[a]":"params['capacities'][position(a)] > 0","cost[a]":"params['costs'][position(a)]; unused in objective","demand[k]":"params['demands'][k] >= 0","source":"{0:3,1:1}","sink":"{0:7,1:5}"},"variables":{"flow[k,i,j]":"nonnegative continuous","peak_utilization":"nonnegative continuous"},"constraints":["For each k,n: sum(flow[k,n,j]) - sum(flow[k,i,n]) = demand[k] if n=source[k], -demand[k] if n=sink[k], else 0.","For each (i,j): sum_k flow[k,i,j] <= capacity[i,j].","For each (i,j): sum_k flow[k,i,j] <= peak_utilization * capacity[i,j]."],"objective":"minimize peak_utilization"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    capacities = params["capacities"]
    costs = params["costs"]
    demands = params["demands"]

    if num_nodes != 8 or num_commodities != 2:
        return {"objective": None, "status": "invalid_dimensions"}

    arcs = [
        (0, 1), (1, 0),
        (0, 3), (3, 0),
        (0, 5), (5, 0),
        (0, 6), (6, 0),
        (0, 7), (7, 0),
        (1, 2), (2, 1),
        (1, 5), (5, 1),
        (1, 6), (6, 1),
        (2, 3), (3, 2),
        (2, 6), (6, 2),
        (3, 4), (4, 3),
        (4, 5), (5, 4),
        (4, 6), (6, 4),
        (4, 7), (7, 4),
        (5, 6), (6, 5),
        (5, 7), (7, 5),
        (6, 7), (7, 6),
    ]

    if (
        len(capacities) != len(arcs)
        or len(costs) != len(arcs)
        or len(demands) != num_commodities
    ):
        return {"objective": None, "status": "invalid_data_lengths"}

    if any(value <= 0 for value in capacities):
        return {"objective": None, "status": "invalid_capacities"}

    if any(value < 0 for value in demands):
        return {"objective": None, "status": "invalid_demands"}

    sources = {0: 3, 1: 1}
    sinks = {0: 7, 1: 5}

    outgoing = {
        node: [end for start, end in arcs if start == node]
        for node in range(num_nodes)
    }
    incoming = {
        node: [start for start, end in arcs if end == node]
        for node in range(num_nodes)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.commodities = pyo.Set(
        initialize=range(num_commodities), ordered=True
    )
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.PositiveReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position]
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
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
    )
    model.peak_utilization = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(network, commodity, node):
        net_outflow = (
            pyo.quicksum(
                network.flow[commodity, node, end]
                for end in outgoing[node]
            )
            - pyo.quicksum(
                network.flow[commodity, start, node]
                for start in incoming[node]
            )
        )

        if node == sources[commodity]:
            required_balance = network.demand[commodity]
        elif node == sinks[commodity]:
            required_balance = -network.demand[commodity]
        else:
            required_balance = 0

        return net_outflow == required_balance

    model.flow_balance = pyo.Constraint(
        model.commodities, model.nodes, rule=balance_rule
    )

    def capacity_rule(network, start, end):
        return (
            pyo.quicksum(
                network.flow[commodity, start, end]
                for commodity in network.commodities
            )
            <= network.capacity[start, end]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def utilization_rule(network, start, end):
        return (
            pyo.quicksum(
                network.flow[commodity, start, end]
                for commodity in network.commodities
            )
            <= network.peak_utilization * network.capacity[start, end]
        )

    model.utilization_limits = pyo.Constraint(
        model.arcs, rule=utilization_rule
    )

    model.objective = pyo.Objective(
        expr=model.peak_utilization,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}