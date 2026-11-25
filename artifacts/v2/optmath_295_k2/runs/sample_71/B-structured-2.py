# IR: {"sets":{"I":"0..8","J":"0..5"},"params":{"fixed_costs":"nonnegative[J]","shipping_costs":"nonnegative[I,J], input rows I and columns J","demands":"nonnegative[I]","capacities":"nonnegative[J]"},"variables":{"opened[J]":"binary","shipped[I,J]":"nonnegative continuous"},"constraints":["For each i: sum_j shipped[i,j] == demands[i]","For each j: sum_i shipped[i,j] <= capacities[j]*opened[j] (enforces activation and capacity)"],"objective":"minimize sum_j fixed_costs[j]*opened[j] + sum_i sum_j shipping_costs[i,j]*shipped[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.customers = pyo.RangeSet(0, 8)
    model.facilities = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, j: fixed_costs[j],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.customers,
        model.facilities,
        initialize=lambda mdl, i, j: shipping_costs[i][j],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, i: demands[i],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda mdl, j: capacities[j],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.customers, model.facilities, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.facilities)
            == mdl.demand[i]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_activation_rule(mdl, j):
        return (
            sum(mdl.shipped[i, j] for i in mdl.customers)
            <= mdl.capacity[j] * mdl.opened[j]
        )

    model.capacity_activation = pyo.Constraint(
        model.facilities, rule=capacity_activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[j] * model.opened[j]
                for j in model.facilities
            )
            + sum(
                model.shipping_cost[i, j] * model.shipped[i, j]
                for i in model.customers
                for j in model.facilities
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A solve without a loaded solution leaves the objective unavailable.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}