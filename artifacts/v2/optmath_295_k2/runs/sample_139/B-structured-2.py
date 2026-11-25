# IR: {"sets":{"H":[0,1,2,3,4],"A":"all ordered pairs (i,j) in H x H with i != j, in lexicographic order","R":"A excluding (0,1) and (0,2)"},"params":{"net_flow_hub0":"net-outflow magnitude at hub 0","net_flow_hub1":"net-outflow magnitude at hub 1","net_flow_hub2":"signed net outflow at hub 2","net_flow_hub3":"net-inflow magnitude at hub 3","net_flow_hub4":"net-inflow magnitude at hub 4","fixed_cost_0_1":"fixed cost for (0,1)","fixed_cost_0_2":"fixed cost for (0,2)","fixed_cost_other":"scalar, arc-keyed mapping, or sequence of exact costs in R order","capacity_0_1":"capacity for (0,1)","capacity_0_2":"capacity for (0,2)","capacity_other":"scalar, arc-keyed mapping, or sequence of exact capacities in R order","variable_cost_0_1":"unit cost for (0,1)","variable_cost_0_2":"unit cost for (0,2)","variable_cost_other":"scalar, arc-keyed mapping, or sequence of exact unit costs in R order"},"derived":{"b":"[abs(net_flow_hub0),abs(net_flow_hub1),net_flow_hub2,-abs(net_flow_hub3),-abs(net_flow_hub4)]"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A","opened[i,j]":"binary for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j]*opened[i,j] for each (i,j) in A","sum_j flow[h,j] - sum_i flow[i,h] = b[h] for each h in H"],"objective":"minimize sum_(i,j in A) fixed_cost[i,j]*opened[i,j] + variable_cost[i,j]*flow[i,j]","input_policy":"Two-element *_other sequences are ranges, not exact arc data; return insufficient_arc_data rather than invent values."}
#
# Assumptions:
# - Every directed connection between distinct hubs is available.
# - The stated net-outflow/net-inflow convention defines the balance signs.
# - A range such as [612, 770] does not specify individual connection costs.
#   Exact optimization requires a scalar shared by all remaining arcs,
#   a complete arc-keyed mapping, or one value per remaining arc.
# - Arc-keyed mappings accept tuple keys (i, j) or string keys "i_j".

from collections.abc import Mapping, Sequence

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


class ArcDataError(ValueError):
    """Expected failure caused by missing or ambiguous connection data."""


def solve(params):
    hubs = tuple(range(5))
    arcs = tuple(
        (origin, destination)
        for origin in hubs
        for destination in hubs
        if origin != destination
    )
    remaining_arcs = tuple(
        arc for arc in arcs if arc not in ((0, 1), (0, 2))
    )

    net_flow_inputs = (
        params["net_flow_hub0"],
        params["net_flow_hub1"],
        params["net_flow_hub2"],
        params["net_flow_hub3"],
        params["net_flow_hub4"],
    )

    fixed_inputs = (
        params["fixed_cost_0_1"],
        params["fixed_cost_0_2"],
        params["fixed_cost_other"],
    )
    capacity_inputs = (
        params["capacity_0_1"],
        params["capacity_0_2"],
        params["capacity_other"],
    )
    variable_inputs = (
        params["variable_cost_0_1"],
        params["variable_cost_0_2"],
        params["variable_cost_other"],
    )

    def expand_arc_data(special_0_1, special_0_2, other):
        values = {
            (0, 1): float(special_0_1),
            (0, 2): float(special_0_2),
        }

        if isinstance(other, Mapping):
            for origin, destination in remaining_arcs:
                arc = (origin, destination)
                string_key = f"{origin}_{destination}"
                if arc in other:
                    value = other[arc]
                elif string_key in other:
                    value = other[string_key]
                else:
                    raise ArcDataError("missing_arc_data")

                if isinstance(value, (Mapping, Sequence)) and not isinstance(
                    value, (str, bytes)
                ):
                    raise ArcDataError("insufficient_arc_data")
                values[arc] = float(value)

        elif isinstance(other, Sequence) and not isinstance(
            other, (str, bytes)
        ):
            if len(other) != len(remaining_arcs):
                raise ArcDataError("insufficient_arc_data")

            for arc, value in zip(remaining_arcs, other):
                if isinstance(value, (Mapping, Sequence)) and not isinstance(
                    value, (str, bytes)
                ):
                    raise ArcDataError("insufficient_arc_data")
                values[arc] = float(value)

        else:
            shared_value = float(other)
            values.update(
                {arc: shared_value for arc in remaining_arcs}
            )

        return values

    try:
        fixed_cost = expand_arc_data(*fixed_inputs)
        capacity = expand_arc_data(*capacity_inputs)
        variable_cost = expand_arc_data(*variable_inputs)
    except ArcDataError as exc:
        return {"objective": None, "status": str(exc)}

    net_outflow = {
        0: abs(float(net_flow_inputs[0])),
        1: abs(float(net_flow_inputs[1])),
        2: float(net_flow_inputs[2]),
        3: -abs(float(net_flow_inputs[3])),
        4: -abs(float(net_flow_inputs[4])),
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=hubs, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_outflow = pyo.Param(
        model.hubs, initialize=net_outflow, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.arcs, initialize=fixed_cost, within=pyo.NonNegativeReals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.variable_cost = pyo.Param(
        model.arcs, initialize=variable_cost, within=pyo.NonNegativeReals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.opened = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
            * network.opened[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, hub):
        outgoing = sum(
            network.flow[hub, destination]
            for destination in hubs
            if destination != hub
        )
        incoming = sum(
            network.flow[origin, hub]
            for origin in hubs
            if origin != hub
        )
        return outgoing - incoming == network.net_outflow[hub]

    model.flow_balance = pyo.Constraint(
        model.hubs, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[origin, destination]
            * model.opened[origin, destination]
            + model.variable_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic loading finds no feasible
        # solution. Objective retrieval below remains the success test.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}