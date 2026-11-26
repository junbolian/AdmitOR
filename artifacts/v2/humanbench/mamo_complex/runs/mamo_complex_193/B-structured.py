# IR: {"sets":{"DC":"0..6","STORE":"0..4"},"params":{"opening_cost":"DC -> real","transport_cost":"DC x STORE -> real","demand":"STORE -> nonnegative real","capacity":"DC -> nonnegative real"},"variables":{"opened":"DC -> binary","shipment":"DC x STORE -> nonnegative real"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i] * opened[i] + sum_i,j transport_cost[i,j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 6)
    model.STORE = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={i: opening_cost[i] for i in model.DC},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.DC
            for j in model.STORE
        },
        within=pyo.Reals,
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

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(problem, j):
        return (
            sum(problem.shipment[i, j] for i in problem.DC)
            == problem.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(problem, i):
        return (
            sum(problem.shipment[i, j] for j in problem.STORE)
            <= problem.capacity[i] * problem.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}