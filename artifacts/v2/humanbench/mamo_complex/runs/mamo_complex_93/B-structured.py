# IR: {"sets":{"I":"range(params['n_centers']); frozen size 8","J":"range(params['n_stores']); frozen size 9"},"params":{"opening_costs":"nonnegative vector indexed by I","transport_costs":"rows [lower_i, upper_i], indexed by I; independent interval for every store","demands":"nonnegative vector indexed by J","capacities":"nonnegative vector indexed by I","n_centers":"frozen center count","n_stores":"frozen store count"},"variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["sum(shipped[i,j] for i in I) == demands[j], for each j in J","sum(shipped[i,j] for j in J) <= capacities[i]*opened[i], for each i in I"],"objective":"minimize sum(opening_costs[i]*opened[i] for i in I) + sum(upper_i*shipped[i,j] for i in I for j in J); robust worst-case cost over independent transportation-cost intervals"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the capacitated facility-location problem with interval costs.

    Expected inputs are ordinary sequences, with transport_costs[i] supplied
    as [lower_cost, upper_cost].

    Because exact store-specific transportation costs are unavailable, this
    model minimizes the worst-case total cost over the supplied independent
    intervals. Nonnegative shipments make every upper endpoint worst-case.
    The returned objective is this robust optimum; the exact nominal optimum
    cannot be identified from interval data alone.
    """
    n_centers = params["n_centers"]
    n_stores = params["n_stores"]
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    if (n_centers, n_stores) != (8, 9):
        return {"objective": None, "status": "invalid_dimensions"}

    if (
        len(opening_costs) != n_centers
        or len(transport_costs) != n_centers
        or len(capacities) != n_centers
        or len(demands) != n_stores
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if any(len(row) != 2 for row in transport_costs):
        return {"objective": None, "status": "invalid_cost_ranges"}

    fixed_cost = [float(value) for value in opening_costs]
    demand = [float(value) for value in demands]
    capacity = [float(value) for value in capacities]
    cost_bounds = [
        (float(row[0]), float(row[1])) for row in transport_costs
    ]

    scalar_values = fixed_cost + demand + capacity
    scalar_values.extend(
        endpoint for bounds in cost_bounds for endpoint in bounds
    )
    if any(
        not math.isfinite(value) or value < 0
        for value in scalar_values
    ):
        return {"objective": None, "status": "invalid_numeric_data"}

    if any(lower > upper for lower, upper in cost_bounds):
        return {"objective": None, "status": "invalid_cost_ranges"}

    model = pyo.ConcreteModel()
    model.centers = pyo.Set(initialize=range(n_centers), ordered=True)
    model.stores = pyo.Set(initialize=range(n_stores), ordered=True)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize={i: fixed_cost[i] for i in range(n_centers)},
        within=pyo.NonNegativeReals,
    )
    model.cost_lower = pyo.Param(
        model.centers,
        initialize={i: cost_bounds[i][0] for i in range(n_centers)},
        within=pyo.NonNegativeReals,
    )
    model.cost_upper = pyo.Param(
        model.centers,
        initialize={i: cost_bounds[i][1] for i in range(n_centers)},
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demand[j] for j in range(n_stores)},
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacity[i] for i in range(n_centers)},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipped[i, j] for i in instance.centers)
            == instance.store_demand[j]
        )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipped[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.opened[i]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.cost_upper[i] * model.shipped[i, j]
                for i in model.centers
                for j in model.stores
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