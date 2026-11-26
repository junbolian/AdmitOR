# IR: {"sets":{"N":"range(params['num_data_centers']); frozen size 8","A":"{(i,j): i in N, j in N\\{0}, i!=j, (i,j)!=(3,6)}","T":"N\\{0,7}"},"params":{"num_data_centers":"params['num_data_centers']","capacity[i,j]":"params[f'capacity_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in T"],"objective":"maximize sum(flow[0,j] for (0,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_data_centers = params["num_data_centers"]
    if num_data_centers != 8:
        raise ValueError("num_data_centers must equal the frozen network size of 8.")

    nodes = tuple(range(int(num_data_centers)))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if destination != 0
        and origin != destination
        and (origin, destination) != (3, 6)
    )
    intermediate_nodes = tuple(node for node in nodes if node not in (0, 7))

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }
    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=intermediate_nodes, ordered=True
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, node):
        return (
            sum(network.flow[arc] for arc in incoming[node])
            == sum(network.flow[arc] for arc in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )
    model.objective = pyo.Objective(
        expr=sum(model.flow[arc] for arc in outgoing[0]),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}