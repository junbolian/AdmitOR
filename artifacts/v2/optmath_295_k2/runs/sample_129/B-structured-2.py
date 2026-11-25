# IR: {"sets":{"F":"range(4)","C":"range(10)"},"params":{"fixed_costs":"F -> nonnegative real","demands":"C -> nonnegative real","shipping_costs":"F x C -> nonnegative real","capacities":"F -> nonnegative real"},"variables":{"is_open[F]":"binary","shipment[F,C]":"nonnegative continuous"},"constraints":["For each customer j: sum_i shipment[i,j] == demands[j].","For each facility i: sum_j shipment[i,j] <= capacities[i] * is_open[i], enforcing both activation and capacity."],"objective":"Minimize sum_i fixed_costs[i]*is_open[i] + sum_i,j shipping_costs[i][j]*shipment[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=range(4), ordered=True)
    model.customers = pyo.Set(initialize=range(10), ordered=True)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda model, i: fixed_costs[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda model, j: demands[j],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize=lambda model, i, j: shipping_costs[i][j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda model, i: capacities[i],
        within=pyo.NonNegativeReals,
    )

    model.is_open = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.facilities)
            == model.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.customers)
            <= model.capacity[i] * model.is_open[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.is_open[i]
                for i in model.facilities
            )
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.facilities
                for j in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when it cannot load a feasible solution.
        # Unexpected runtime errors must still propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}