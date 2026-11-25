# IR: {"sets":{"N":[0,1,2,3,4],"A":"all ordered pairs (i,j) with i != j","E_other":"lexicographically ordered pairs (i,j) with i < j, excluding (0,1) and (0,2)","A_other":"lexicographically ordered arcs excluding both directions of (0,1) and (0,2)"},"params":["net_flow_hub0","net_flow_hub1","net_flow_hub2","net_flow_hub3","net_flow_hub4","fixed_cost_0_1","fixed_cost_0_2","fixed_cost_other","capacity_0_1","capacity_0_2","capacity_other","variable_cost_0_1","variable_cost_0_2","variable_cost_other"],"assumptions":["Every directed arc has its own establishment decision.","The two named connection parameters apply in both directions.","Each *_other input may be a scalar, an eight-element sequence indexed by E_other, a sixteen-element sequence indexed by A_other, or a dictionary keyed by hub-pair tuples; unordered pair data apply in both directions.","Positive net outflow is used at hubs 0 and 1; supplied inflow magnitudes are negated at hubs 3 and 4."],"derived_params":{"b":"[net_flow_hub0,net_flow_hub1,net_flow_hub2,-net_flow_hub3,-net_flow_hub4]","F[i,j]":"fixed cost expanded from the named connection parameters and fixed_cost_other","U[i,j]":"capacity expanded from the named connection parameters and capacity_other","C[i,j]":"variable cost expanded from the named connection parameters and variable_cost_other"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A","established[i,j]":"binary, (i,j) in A"},"constraints":["flow[i,j] <= U[i,j]*established[i,j] for every (i,j) in A","sum(flow[i,j] for j != i)-sum(flow[j,i] for j != i) == b[i] for every i in N"],"objective":"minimize sum(F[i,j]*established[i,j]+C[i,j]*flow[i,j] for (i,j) in A)"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _expand_parameter(
    special_0_1,
    special_0_2,
    other,
    arcs,
    other_pairs,
    other_arcs,
    parameter_name,
):
    """Convert scalar or indexed connection data into numeric arc values."""
    values = {
        (0, 1): float(special_0_1),
        (1, 0): float(special_0_1),
        (0, 2): float(special_0_2),
        (2, 0): float(special_0_2),
    }

    if isinstance(other, Mapping):
        for origin, destination in other_arcs:
            arc = (origin, destination)
            reverse_arc = (destination, origin)
            if arc in other:
                values[arc] = float(other[arc])
            elif reverse_arc in other:
                values[arc] = float(other[reverse_arc])
            else:
                raise ValueError(
                    f"{parameter_name} is missing connection {arc}."
                )
    elif isinstance(other, Number):
        numeric_value = float(other)
        for arc in other_arcs:
            values[arc] = numeric_value
    else:
        if isinstance(other, (str, bytes)):
            raise TypeError(
                f"{parameter_name} must be numeric, a sequence, or a mapping."
            )

        entries = list(other)

        if len(entries) == len(other_pairs):
            for (origin, destination), entry in zip(other_pairs, entries):
                numeric_value = float(entry)
                values[origin, destination] = numeric_value
                values[destination, origin] = numeric_value
        elif len(entries) == len(other_arcs):
            for arc, entry in zip(other_arcs, entries):
                values[arc] = float(entry)
        else:
            raise ValueError(
                f"{parameter_name} must contain {len(other_pairs)} "
                f"unordered connection values or {len(other_arcs)} "
                "directed arc values."
            )

    return {arc: values[arc] for arc in arcs}


def solve(params):
    nodes = tuple(range(5))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )

    special_pairs = {(0, 1), (0, 2)}
    other_pairs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin < destination
        and (origin, destination) not in special_pairs
    )
    other_arcs = tuple(
        (origin, destination)
        for origin, destination in arcs
        if (min(origin, destination), max(origin, destination))
        not in special_pairs
    )

    net_outflow = {
        0: float(params["net_flow_hub0"]),
        1: float(params["net_flow_hub1"]),
        2: float(params["net_flow_hub2"]),
        3: -float(params["net_flow_hub3"]),
        4: -float(params["net_flow_hub4"]),
    }

    fixed_cost = _expand_parameter(
        params["fixed_cost_0_1"],
        params["fixed_cost_0_2"],
        params["fixed_cost_other"],
        arcs,
        other_pairs,
        other_arcs,
        "fixed_cost_other",
    )
    capacity = _expand_parameter(
        params["capacity_0_1"],
        params["capacity_0_2"],
        params["capacity_other"],
        arcs,
        other_pairs,
        other_arcs,
        "capacity_other",
    )
    variable_cost = _expand_parameter(
        params["variable_cost_0_1"],
        params["variable_cost_0_2"],
        params["variable_cost_other"],
        arcs,
        other_pairs,
        other_arcs,
        "variable_cost_other",
    )

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_outflow = pyo.Param(
        model.hubs, initialize=net_outflow, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.arcs, initialize=fixed_cost, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.variable_cost = pyo.Param(
        model.arcs, initialize=variable_cost, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.established = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
            * network.established[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, hub):
        outgoing = sum(
            network.flow[hub, destination]
            for destination in network.hubs
            if destination != hub
        )
        incoming = sum(
            network.flow[origin, hub]
            for origin in network.hubs
            if origin != hub
        )
        return outgoing - incoming == network.net_outflow[hub]

    model.flow_balances = pyo.Constraint(
        model.hubs, rule=balance_rule
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}