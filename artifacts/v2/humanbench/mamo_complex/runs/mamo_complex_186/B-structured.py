# IR: {"sets":{"I":"1..9","J":"1..5"},"params":{"opening_cost":"I, from params['opening_cost'][i-1]","transport_cost":"I x J, from params['transport_cost'][i-1][j-1]","demand":"J, from params['demand'][j-1]","capacity":"I, from params['capacity'][i-1]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each j in J: sum(shipment[i,j] for i in I) == demand[j]","For each i in I: sum(shipment[i,j] for j in J) <= capacity[i]*opened[i]"],"objective":"Minimize sum(opening_cost[i]*opened[i] for i in I) + sum(transport_cost[i,j]*shipment[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(1, 9)
    model.J = pyo.RangeSet(1, 5)

    model.opening_cost = pyo.Param(
        model.I,
        initialize=lambda model, i: params["opening_cost"][i - 1],
    )
    model.transport_cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda model, i, j: params["transport_cost"][i - 1][j - 1],
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda model, j: params["demand"][j - 1],
    )
    model.capacity = pyo.Param(
        model.I,
        initialize=lambda model, i: params["capacity"][i - 1],
    )

    model.opened = pyo.Var(model.I, domain=pyo.Binary)
    model.shipment = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.I)
            == model.demand[j]
        )

    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)

    def capacity_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.J)
            <= model.capacity[i] * model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.I, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.I
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.I
                for j in model.J
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}