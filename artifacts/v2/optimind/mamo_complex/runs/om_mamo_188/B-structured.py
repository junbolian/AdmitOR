# IR: {"sets":{"DC":"1..5","STORE":"1..7"},"params":{"opening_cost":"opening_cost[i], supplied as a length-5 array","transport_cost":"transport_cost[i,j], supplied as a 5x7 array","demand":"demand[j], supplied as a length-7 array","capacity":"capacity[i], supplied as a length-5 array"},"variables":{"is_open[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each j: sum_i shipment[i,j] == demand[j]","For each i: sum_j shipment[i,j] <= capacity[i] * is_open[i]"],"objective":"Minimize sum_i opening_cost[i]*is_open[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based Python arrays for all parameter inputs."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(1, 5)
    model.STORE = pyo.RangeSet(1, 7)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize=lambda mdl, i: opening_cost[i - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=lambda mdl, i, j: transport_cost[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize=lambda mdl, j: demand[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize=lambda mdl, i: capacity[i - 1],
        within=pyo.NonNegativeReals,
    )

    model.is_open = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.DC) == mdl.demand[j]

    model.demand_fulfillment = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.STORE)
            <= mdl.capacity[i] * mdl.is_open[i]
        )

    model.capacity_limits = pyo.Constraint(model.DC, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.is_open[i]
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