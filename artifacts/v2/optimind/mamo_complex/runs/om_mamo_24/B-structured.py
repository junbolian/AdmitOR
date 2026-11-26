# IR: {"sets":{"centers":"0..6","stores":"0..4"},"params":{"opening_costs":"params['opening_costs'][i]","transport_costs":"params['transport_costs'][i][j]","demands":"params['demands'][j]","capacities":"params['capacities'][i]"},"variables":{"opened[i]":"binary","shipped[i,j]":"nonnegative continuous"},"constraints":["For each store j: sum_i shipped[i,j] = demands[j]","For each center i: sum_j shipped[i,j] <= capacities[i] * opened[i]"],"objective":"Minimize sum_i opening_costs[i] * opened[i] + sum_i,j transport_costs[i][j] * shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based sequences; transport_costs is center-by-store."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 6)
    model.stores = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda _, i: opening_costs[i],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda _, i, j: transport_costs[i][j],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda _, j: demands[j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda _, i: capacities[i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(_, j):
        return (
            sum(model.shipped[i, j] for i in model.centers)
            == model.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(_, i):
        return (
            sum(model.shipped[i, j] for j in model.stores)
            <= model.capacity[i] * model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}