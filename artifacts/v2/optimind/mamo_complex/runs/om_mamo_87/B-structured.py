# IR: {"sets":{"centers":"0..7","stores":"0..7"},"params":{"opening_cost":"opening_cost[i]","transport_cost":"transport_cost[i][j]","demand":"demand[j]","capacity":"capacity[i]"},"variables":{"opened[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i][j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 7)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize=lambda _, i: opening_cost[i],
    )
    model.unit_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda _, i, j: transport_cost[i][j],
    )
    model.required_units = pyo.Param(
        model.stores,
        initialize=lambda _, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.available_units = pyo.Param(
        model.centers,
        initialize=lambda _, i: capacity[i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(problem, j):
        return (
            sum(problem.shipment[i, j] for i in problem.centers)
            == problem.required_units[j]
        )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=demand_rule,
    )

    def capacity_rule(problem, i):
        return (
            sum(problem.shipment[i, j] for j in problem.stores)
            <= problem.available_units[i] * problem.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.unit_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}