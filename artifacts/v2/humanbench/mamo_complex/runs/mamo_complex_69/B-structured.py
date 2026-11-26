# IR: {"sets":{"centers":"0..5","stores":"0..7"},"params":{"opening_costs":"required length-6 numeric array","transport_costs":"required complete 6x8 numeric array; unspecified entries are not inferred","demands":"required length-8 nonnegative numeric array","capacities":"required length-6 nonnegative numeric array"},"variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipped[i,j] == demands[j]","For each center i: sum_j shipped[i,j] <= capacities[i]*opened[i]"],"objective":"Minimize sum_i opening_costs[i]*opened[i] + sum_i,j transport_costs[i][j]*shipped[i,j]","missing_input":"Return objective null and status missing_parameter:<key>; no costs are fabricated."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_keys = (
        "opening_costs",
        "transport_costs",
        "demands",
        "capacities",
    )
    for key in required_keys:
        if key not in params or params[key] is None:
            return {
                "objective": None,
                "status": "missing_parameter:" + key,
            }

    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    # A numerical optimum requires every transportation cost. The partial
    # examples in the problem do not determine the missing matrix entries.
    if len(opening_costs) != 6:
        return {"objective": None, "status": "invalid_opening_costs"}
    if len(demands) != 8:
        return {"objective": None, "status": "invalid_demands"}
    if len(capacities) != 6:
        return {"objective": None, "status": "invalid_capacities"}
    if len(transport_costs) != 6:
        return {"objective": None, "status": "incomplete_transport_costs"}
    for row in transport_costs:
        if row is None or len(row) != 8:
            return {"objective": None, "status": "incomplete_transport_costs"}
        if any(cost is None for cost in row):
            return {"objective": None, "status": "incomplete_transport_costs"}

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: opening_costs[i],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: transport_costs[i][j],
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demands[j],
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: capacities[i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipped[i, j] for i in mdl.centers)
            == mdl.store_demand[j]
        )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.stores)
            <= mdl.center_capacity[i] * mdl.opened[i]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipped[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}