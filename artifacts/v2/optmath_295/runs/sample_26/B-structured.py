# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3]},"params":{"capacity":"capacity[i]","demand":"demand[j]","min_delivery":"min_delivery[i]","cost":"cost[i][j]"},"variables":{"delivery[i,j]":"NonNegativeReals","contributes[i,j]":"Binary"},"constraints":["sum(delivery[i,j] for j in J) <= capacity[i] for i in I","sum(delivery[i,j] for i in I) >= demand[j] for j in J","sum(contributes[i,j] for i in I) >= 2 for j in J","delivery[i,j] >= min_delivery[i]*contributes[i,j] for i in I,j in J","delivery[i,j] <= capacity[i]*contributes[i,j] for i in I,j in J"],"objective":"minimize sum(cost[i][j]*delivery[i,j] for i in I,j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.J = pyo.RangeSet(0, 3)

    model.capacity = pyo.Param(
        model.I, initialize=lambda model, i: capacity[i]
    )
    model.demand = pyo.Param(
        model.J, initialize=lambda model, j: demand[j]
    )
    model.min_delivery = pyo.Param(
        model.I, initialize=lambda model, i: min_delivery[i]
    )
    model.cost = pyo.Param(
        model.I, model.J,
        initialize=lambda model, i, j: cost[i][j],
    )

    model.delivery = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.I, model.J, domain=pyo.Binary
    )

    model.capacity_limit = pyo.Constraint(
        model.I,
        rule=lambda model, i: (
            sum(model.delivery[i, j] for j in model.J)
            <= model.capacity[i]
        ),
    )

    model.demand_requirement = pyo.Constraint(
        model.J,
        rule=lambda model, j: (
            sum(model.delivery[i, j] for i in model.I)
            >= model.demand[j]
        ),
    )

    model.producer_requirement = pyo.Constraint(
        model.J,
        rule=lambda model, j: (
            sum(model.contributes[i, j] for i in model.I) >= 2
        ),
    )

    model.minimum_contribution = pyo.Constraint(
        model.I, model.J,
        rule=lambda model, i, j: (
            model.delivery[i, j]
            >= model.min_delivery[i] * model.contributes[i, j]
        ),
    )

    model.contribution_link = pyo.Constraint(
        model.I, model.J,
        rule=lambda model, i, j: (
            model.delivery[i, j]
            <= model.capacity[i] * model.contributes[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.delivery[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}