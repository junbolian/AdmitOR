# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4],"K":[0,1]},"params":{"supply":"params['supply'][i][k]","demand":"params['demand'][j][k]","cost":"params['cost'][i][j][k]","capacity":"params['capacity'][i][j]"},"variables":{"shipment[i,j,k]":"nonnegative continuous"},"constraints":["sum(j in J, shipment[i,j,k]) == supply[i,k] for i in I, k in K","sum(i in I, shipment[i,j,k]) == demand[j,k] for j in J, k in K","sum(k in K, shipment[i,j,k]) <= capacity[i,j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, k in K, cost[i,j,k] * shipment[i,j,k])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(4), ordered=True)
    model.J = pyo.Set(initialize=range(5), ordered=True)
    model.K = pyo.Set(initialize=range(2), ordered=True)

    model.supply = pyo.Param(
        model.I,
        model.K,
        initialize=lambda model, i, k: supply[i][k],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        model.K,
        initialize=lambda model, j, k: demand[j][k],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        model.K,
        initialize=lambda model, i, j, k: cost[i][j][k],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize=lambda model, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.I, model.J, model.K, domain=pyo.NonNegativeReals
    )

    def supply_rule(model, i, k):
        return (
            sum(model.shipment[i, j, k] for j in model.J)
            == model.supply[i, k]
        )

    model.supply_balance = pyo.Constraint(
        model.I, model.K, rule=supply_rule
    )

    def demand_rule(model, j, k):
        return (
            sum(model.shipment[i, j, k] for i in model.I)
            == model.demand[j, k]
        )

    model.demand_balance = pyo.Constraint(
        model.J, model.K, rule=demand_rule
    )

    def capacity_rule(model, i, j):
        return (
            sum(model.shipment[i, j, k] for k in model.K)
            <= model.capacity[i, j]
        )

    model.route_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j, k] * model.shipment[i, j, k]
            for i in model.I
            for j in model.J
            for k in model.K
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}