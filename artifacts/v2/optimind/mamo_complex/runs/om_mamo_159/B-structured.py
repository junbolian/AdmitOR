# IR: {"sets":{"I":"0..7","J":"0..8"},"params":{"opening_costs":"USD[I]","transport_costs":"USD/unit[I,J]","demands":"units[J]","capacities":"units[I]"},"variables":{"opened[I]":"binary","shipped[I,J]":"continuous nonnegative"},"constraints":["For each j in J: sum(i in I, shipped[i,j]) = demands[j]","For each i in I: sum(j in J, shipped[i,j]) <= capacities[i] * opened[i]"],"objective":"minimize sum(i in I, opening_costs[i] * opened[i]) + sum(i in I,j in J, transport_costs[i,j] * shipped[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 8)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: opening_costs[i],
    )
    model.shipping_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: transport_costs[i][j],
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demands[j],
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: capacities[i],
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return sum(
            mdl.shipped[i, j] for i in mdl.centers
        ) == mdl.store_demand[j]

    model.demand_fulfillment = pyo.Constraint(
        model.stores,
        rule=demand_rule,
    )

    def capacity_rule(mdl, i):
        return sum(
            mdl.shipped[i, j] for j in mdl.stores
        ) <= mdl.center_capacity[i] * mdl.opened[i]

    model.capacity_limits = pyo.Constraint(
        model.centers,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i] * model.opened[i]
            for i in model.centers
        )
        + sum(
            model.shipping_cost[i, j] * model.shipped[i, j]
            for i in model.centers
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}