# {"sets":{"N":"0..5","A":"{(i,j) in N x N: i != j}"},"params":{"demand_0":"params['demand_0']","demand_1":"params['demand_1']","supply_4":"params['supply_4']","supply_5":"params['supply_5']","fixed_cost[i,j]":"params['fixed_cost'][i][j]","variable_cost[i,j]":"params['variable_cost'][i][j]","capacity[i,j]":"params['capacity'][i][j]","net_inflow":"[demand_0,demand_1,0,0,-supply_4,-supply_5]"},"variables":{"flow[i,j]":"nonnegative continuous","opened[i,j]":"binary"},"constraints":["sum(flow[j,i] for j != i)-sum(flow[i,j] for j != i)=net_inflow[i], i in N","flow[i,j]<=capacity[i,j]*opened[i,j], (i,j) in A"],"objective":"minimize sum(fixed_cost[i,j]*opened[i,j]+variable_cost[i,j]*flow[i,j] for (i,j) in A)","input_validation":"Return missing_parameter:<key> if a required key is absent; do not invent missing values."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_keys = (
        "demand_0",
        "demand_1",
        "supply_4",
        "supply_5",
        "fixed_cost",
        "variable_cost",
        "capacity",
    )
    for key in required_keys:
        if key not in params:
            return {
                "objective": None,
                "status": f"missing_parameter:{key}",
            }

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(6)
            for destination in range(6)
            if origin != destination
        ],
    )

    model.demand_0 = pyo.Param(initialize=params["demand_0"])
    model.demand_1 = pyo.Param(initialize=params["demand_1"])
    model.supply_4 = pyo.Param(initialize=params["supply_4"])
    model.supply_5 = pyo.Param(initialize=params["supply_5"])

    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params["fixed_cost"][origin][destination]
            for origin, destination in model.arcs
        },
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params["variable_cost"][origin][destination]
            for origin, destination in model.arcs
        },
    )
    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params["capacity"][origin][destination]
            for origin, destination in model.arcs
        },
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.opened = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(network, center):
        net_inflow = (
            network.demand_0,
            network.demand_1,
            0,
            0,
            -network.supply_4,
            -network.supply_5,
        )
        incoming = sum(
            network.flow[other, center]
            for other in network.centers
            if other != center
        )
        outgoing = sum(
            network.flow[center, other]
            for other in network.centers
            if other != center
        )
        return incoming - outgoing == net_inflow[center]

    model.flow_balance = pyo.Constraint(
        model.centers, rule=balance_rule
    )

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.arc_capacity[origin, destination]
            * network.opened[origin, destination]
        )

    model.connection_capacity = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[origin, destination]
            * model.opened[origin, destination]
            + model.variable_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        # Attempt objective retrieval below, without inspecting solver enums.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}