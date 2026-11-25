# IR: {"sets":{"H":[0,1,2,3,4],"A":"all ordered pairs (i,j) in H x H with i != j, lexicographically ordered"},"params":{"net_demand":"[params['demand_hub0'],params['demand_hub1'],-params['supply_hub2'],-params['supply_hub3'],-params['supply_hub4']]","fixed_cost":"interpolate params['fixed_cost_range'] by arc rank","variable_cost":"interpolate params['variable_cost_range'] by arc rank","capacity":"interpolate params['capacity_range'] by arc rank","interpolation":"lo + (hi-lo)*rank/(len(A)-1), with zero-based rank"},"variables":{"established[i,j]":"binary for (i,j) in A","flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j]*established[i,j] for every arc","sum_i flow[i,h] - sum_j flow[h,j] = net_demand[h] for every hub"],"objective":"minimize sum_(i,j) fixed_cost[i,j]*established[i,j] + variable_cost[i,j]*flow[i,j]"}
#
# Modeling assumptions: connections are directed, and the stated supplies
# are net outflow requirements, consistent with the requested balance equalities.
# Ranges alone do not specify pair-specific data. This implementation assigns
# each range deterministically by linear interpolation over ordered arcs.
# This assignment is an explicit assumption, not supplied pair-specific data.

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_hub0 = float(params["demand_hub0"])
    demand_hub1 = float(params["demand_hub1"])
    supply_hub2 = float(params["supply_hub2"])
    supply_hub3 = float(params["supply_hub3"])
    supply_hub4 = float(params["supply_hub4"])

    fixed_cost_range = tuple(float(v) for v in params["fixed_cost_range"])
    variable_cost_range = tuple(float(v) for v in params["variable_cost_range"])
    capacity_range = tuple(float(v) for v in params["capacity_range"])

    hub_quantities = (
        demand_hub0,
        demand_hub1,
        supply_hub2,
        supply_hub3,
        supply_hub4,
    )
    ranges = (fixed_cost_range, variable_cost_range, capacity_range)

    if any(not math.isfinite(v) or v < 0 for v in hub_quantities):
        return {"objective": None, "status": "invalid_parameters"}

    for bounds in ranges:
        if (
            len(bounds) != 2
            or any(not math.isfinite(v) or v < 0 for v in bounds)
            or bounds[0] > bounds[1]
        ):
            return {"objective": None, "status": "invalid_parameters"}

    hubs = tuple(range(5))
    arcs = tuple(
        (source, destination)
        for source in hubs
        for destination in hubs
        if source != destination
    )

    net_demand = {
        0: demand_hub0,
        1: demand_hub1,
        2: -supply_hub2,
        3: -supply_hub3,
        4: -supply_hub4,
    }

    def interpolate(bounds):
        lower, upper = bounds
        return {
            arc: lower + (upper - lower) * rank / (len(arcs) - 1)
            for rank, arc in enumerate(arcs)
        }

    model = pyo.ConcreteModel()

    model.hubs = pyo.Set(initialize=hubs, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_demand = pyo.Param(
        model.hubs, initialize=net_demand, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize=interpolate(fixed_cost_range),
        within=pyo.NonNegativeReals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize=interpolate(variable_cost_range),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=interpolate(capacity_range),
        within=pyo.NonNegativeReals,
    )

    model.established = pyo.Var(model.arcs, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
            * network.established[source, destination]
        )

    model.connection_capacity = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, hub):
        inflow = sum(
            network.flow[source, hub]
            for source in network.hubs
            if source != hub
        )
        outflow = sum(
            network.flow[hub, destination]
            for destination in network.hubs
            if destination != hub
        )
        return inflow - outflow == network.net_demand[hub]

    model.flow_balance = pyo.Constraint(model.hubs, rule=balance_rule)

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
        # APPsi raises this when automatic solution loading finds no solution.
        # Re-raise unrelated exceptions so unexpected errors remain visible.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}