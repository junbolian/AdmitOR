# IR: {"sets":{"nodes":[0,1,2,3],"arcs":"all ordered pairs (i,j) of distinct nodes, in lexicographic order"},"params":{"net_demand":"node-indexed input array","fixed_cost":"arc-indexed input array","variable_cost":"arc-indexed input array","capacity":"arc-indexed nonnegative input array"},"variables":{"flow[i,j]":"NonNegativeReals","established[i,j]":"Binary"},"constraints":["For each arc (i,j): flow[i,j] <= capacity[i,j] * established[i,j]","For each node i: sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) == net_demand[i]"],"objective":"Minimize sum(fixed_cost[i,j] * established[i,j] + variable_cost[i,j] * flow[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(4))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )

    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_demand = pyo.Param(
        model.nodes,
        initialize={node: net_demand[node] for node in nodes},
        within=pyo.Reals,
    )
    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={arc: fixed_cost[position] for position, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: variable_cost[position] for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity[position] for position, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.established = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.flow[origin, destination]
            <= mdl.capacity[origin, destination]
            * mdl.established[origin, destination]
        )

    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(mdl, node):
        incoming = sum(
            mdl.flow[other, node]
            for other in mdl.nodes
            if other != node
        )
        outgoing = sum(
            mdl.flow[node, other]
            for other in mdl.nodes
            if other != node
        )
        return incoming - outgoing == mdl.net_demand[node]

    model.balance_constraints = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[origin, destination]
            * model.established[origin, destination]
            + model.variable_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}