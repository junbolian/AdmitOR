# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7,8],"intermediate_nodes":[1,2,3,4,5,6,7],"arcs":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"coordinates":"params['coordinates'][node]; geographic metadata","capacity[i,j]":"params[f'capacity_{i}_{j}']; nonnegative channel limit","cost[i,j]":"params[f'cost_{i}_{j}']; channel cost metadata, unused in the stated maximum-flow objective"},"variables":{"flow[i,j]":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for every arc (i,j)","sum(flow[i,v] for incoming arcs) == sum(flow[v,j] for outgoing arcs) for every intermediate node v"],"objective":"maximize sum(flow[0,j] for arcs leaving node 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(9))
    intermediate_nodes = tuple(range(1, 8))
    arcs = (
        (0, 1),
        (0, 2),
        (0, 6),
        (0, 8),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
    )

    coordinates = params["coordinates"]
    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    costs = {
        (tail, head): params[f"cost_{tail}_{head}"]
        for tail, head in arcs
    }

    incoming = {
        node: tuple((tail, head) for tail, head in arcs if head == node)
        for node in nodes
    }
    outgoing = {
        node: tuple((tail, head) for tail, head in arcs if tail == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=intermediate_nodes, ordered=True
    )
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.coordinates = pyo.Param(
        model.nodes,
        initialize=lambda mdl, node: coordinates[node],
        within=pyo.Any,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, tail, head):
        return mdl.flow[tail, head] <= mdl.capacity[tail, head]

    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(mdl, node):
        return (
            sum(mdl.flow[tail, head] for tail, head in incoming[node])
            == sum(mdl.flow[tail, head] for tail, head in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_settlement = pyo.Objective(
        expr=sum(model.flow[tail, head] for tail, head in outgoing[0]),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # If no solution was loaded, objective evaluation below will fail.
        pass

    try:
        obj_val = float(pyo.value(model.total_settlement))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}