# IR: {"sets":{"DC":"0..7","STORE":"0..4"},"params":{"opening_cost":"nonnegative array[8]","transport_cost":"nonnegative array[8][5]","demand":"nonnegative array[5]","capacity":"nonnegative array[8]"},"variables":{"open_dc[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["sum(i in DC, shipment[i,j]) == demand[j] for each j in STORE","sum(j in STORE, shipment[i,j]) <= capacity[i]*open_dc[i] for each i in DC"],"objective":"minimize sum(i in DC, opening_cost[i]*open_dc[i]) + sum(i in DC,j in STORE, transport_cost[i,j]*shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-indexed input arrays supplied in params."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 7)
    model.STORE = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={i: opening_cost[i] for i in model.DC},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.DC
            for j in model.STORE
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize={j: demand[j] for j in model.STORE},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize={i: capacity[i] for i in model.DC},
        within=pyo.NonNegativeReals,
    )

    model.open_dc = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.DC)
            == instance.demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.STORE)
            <= instance.capacity[i] * instance.open_dc[i]
        )

    model.capacity_constraints = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.open_dc[i]
                for i in model.DC
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.DC
                for j in model.STORE
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
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}