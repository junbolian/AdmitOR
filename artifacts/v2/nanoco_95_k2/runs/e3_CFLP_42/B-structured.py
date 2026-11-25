# IR: {"sets":{"I":"1..20 hospitals","J":"1..5 centers"},"params":{"opening_cost[j]":"params['opening_cost'][j-1]","capacity[j]":"params['capacity'][j-1]","demand[i]":"params['demand'][i-1]","transport_cost[i,j]":"params['transport_cost'][i-1][j-1]"},"variables":{"opened[j]":"binary","assigned[i,j]":"binary"},"constraints":["For each i: sum_j assigned[i,j] = 1","For each j: sum_i demand[i]*assigned[i,j] <= capacity[j]*opened[j]","For each i,j: assigned[i,j] <= opened[j]"],"objective":"minimize sum_j opening_cost[j]*opened[j] + sum_i,j demand[i]*transport_cost[i,j]*assigned[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences and a nested transport-cost matrix."""
    opening_cost = params["opening_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.hospitals = pyo.RangeSet(1, 20)
    model.centers = pyo.RangeSet(1, 5)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda model, j: opening_cost[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda model, j: capacity[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.hospitals,
        initialize=lambda model, i: demand[i - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.hospitals,
        model.centers,
        initialize=lambda model, i, j: transport_cost[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.hospitals, model.centers, domain=pyo.Binary
    )

    def single_source_rule(model, i):
        return sum(model.assigned[i, j] for j in model.centers) == 1

    model.single_source = pyo.Constraint(
        model.hospitals, rule=single_source_rule
    )

    def capacity_rule(model, j):
        return (
            sum(
                model.demand[i] * model.assigned[i, j]
                for i in model.hospitals
            )
            <= model.capacity[j] * model.opened[j]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    def opening_link_rule(model, i, j):
        return model.assigned[i, j] <= model.opened[j]

    model.opening_link = pyo.Constraint(
        model.hospitals, model.centers, rule=opening_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[j] * model.opened[j]
                for j in model.centers
            )
            + sum(
                model.demand[i]
                * model.transport_cost[i, j]
                * model.assigned[i, j]
                for i in model.hospitals
                for j in model.centers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}