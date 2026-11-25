# IR: {"sets":{"N":[0,1,2,3],"A":"[(i,j) for i in N for j in N if i != j], in lexicographic order"},"params":{"net_demand":"params['net_demand'][i] for i in N","fixed_cost":"params['fixed_cost'][k] for the kth arc in A","variable_cost":"params['variable_cost'][k] for the kth arc in A","capacity":"params['capacity'][k] for the kth arc in A"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A","established[i,j]":"Binary for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] * established[i,j] for (i,j) in A","sum(flow[j,i] for j in N if j != i) - sum(flow[i,j] for j in N if j != i) == net_demand[i] for i in N"],"objective":"minimize sum(fixed_cost[i,j]*established[i,j] + variable_cost[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(4))
    arcs = tuple(
        (source, destination)
        for source in nodes
        for destination in nodes
        if source != destination
    )

    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_demand = pyo.Param(
        model.nodes,
        initialize={node: net_demand[node] for node in nodes},
        within=pyo.Reals,
    )
    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={arc: fixed_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={arc: variable_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity[k] for k, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.established = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
            * network.established[source, destination]
        )

    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, node):
        incoming = sum(
            network.flow[other, node]
            for other in network.nodes
            if other != node
        )
        outgoing = sum(
            network.flow[node, other]
            for other in network.nodes
            if other != node
        )
        return incoming - outgoing == network.net_demand[node]

    model.balance_constraints = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[source, destination]
            * model.established[source, destination]
            + model.variable_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in model.arcs
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