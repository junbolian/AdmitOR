# IR: {"sets":{"centers":"0..5","stores":"0..3"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"opened[i]":"binary","shipped[i,j]":"nonnegative continuous"},"constraints":["sum_i shipped[i,j] = demand[j] for each store j","sum_j shipped[i,j] <= capacity[i]*opened[i] for each center i"],"objective":"minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i][j]*shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 3)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda _, i: params["opening_cost"][i],
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda _, i, j: params["transport_cost"][i][j],
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda _, j: params["demand"][j],
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda _, i: params["capacity"][i],
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipped[i, j] for i in instance.centers)
            == instance.demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipped[i, j] for j in instance.stores)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipped[i, j]
                for i in model.centers
                for j in model.stores
            )
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