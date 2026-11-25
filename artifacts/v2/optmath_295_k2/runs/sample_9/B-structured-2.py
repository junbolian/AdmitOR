# IR: {"sets":{"N":"0..6","A":"for i=0..6, j=i+1..6, append (i,j), then (j,i)"},"params":{"node_net_outflow":"real[N], from params","fixed_cost":"real[A], from params in A order","variable_cost":"real[A], from params in A order","capacity":"nonnegative real[A], from params in A order"},"variables":{"flow":"nonnegative continuous[A]","established":"binary[A]"},"constraints":["For each i in N: sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = node_net_outflow[i]","For each (i,j) in A: flow[i,j] <= capacity[i,j] * established[i,j]"],"objective":"minimize sum(fixed_cost[i,j]*established[i,j] + variable_cost[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [
        arc
        for source in nodes
        for destination in range(source + 1, 7)
        for arc in ((source, destination), (destination, source))
    ]

    net_outflow_data = params["node_net_outflow"]
    fixed_cost_data = params["fixed_cost"]
    variable_cost_data = params["variable_cost"]
    capacity_data = params["capacity"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.node_net_outflow = pyo.Param(
        model.nodes,
        initialize={node: net_outflow_data[node] for node in nodes},
        within=pyo.Reals,
    )
    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: fixed_cost_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: variable_cost_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacity_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.established = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(network, node):
        # Positive net outflow denotes supply; negative denotes demand.
        return (
            sum(
                network.flow[node, other]
                for other in network.nodes
                if other != node
            )
            - sum(
                network.flow[other, node]
                for other in network.nodes
                if other != node
            )
            == network.node_net_outflow[node]
        )

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
            * network.established[source, destination]
        )

    model.capacity_link = pyo.Constraint(model.arcs, rule=capacity_rule)

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
        # Appsi raises this when automatic solution loading finds no solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}