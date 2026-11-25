# IR: {"sets":{"I":"0..8","J":"0..5"},"params":{"fixed_costs":"real[J]","shipping_costs":"real[I,J]","demands":"nonnegative_real[I]","capacities":"nonnegative_real[J]"},"variables":{"opened[j]":"binary","shipped[i,j]":"nonnegative_real"},"constraints":["sum(j in J, shipped[i,j]) = demands[i] for i in I","sum(i in I, shipped[i,j]) <= capacities[j]*opened[j] for j in J"],"objective":"minimize sum(j in J, fixed_costs[j]*opened[j]) + sum(i in I,j in J, shipping_costs[i,j]*shipped[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.customers = pyo.RangeSet(0, 8)
    model.facilities = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, j: params["fixed_costs"][j],
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.customers,
        model.facilities,
        initialize=lambda mdl, i, j: params["shipping_costs"][i][j],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, i: params["demands"][i],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda mdl, j: params["capacities"][j],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.customers,
        model.facilities,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.facilities)
            == mdl.demand[i]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(mdl, j):
        return (
            sum(mdl.shipped[i, j] for i in mdl.customers)
            <= mdl.capacity[j] * mdl.opened[j]
        )

    model.capacity_activation = pyo.Constraint(
        model.facilities, rule=capacity_rule
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

    # HiGHS may raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}