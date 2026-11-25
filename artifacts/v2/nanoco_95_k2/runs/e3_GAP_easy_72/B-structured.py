# IR: {"sets":{"centers":["DC1","DC2","DC3"],"orders":[1,2,3,4,5,6,7]},"params":{"capacity[center]":"params['capacity_'+center]","storage[center,order]":"params['storage_'+center][order-1]","cost[center,order]":"params['cost_'+center][order-1]"},"variables":{"assignment[center,order]":"Binary; 1 means order is assigned to center"},"constraints":["For each order: sum(assignment[center,order] for center in centers) == 1","For each center: sum(storage[center,order]*assignment[center,order] for order in orders) <= capacity[center]"],"objective":"Minimize sum(cost[center,order]*assignment[center,order] for center in centers for order in orders)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the allocation problem; storage and cost inputs are ordered sequences."""
    centers = ("DC1", "DC2", "DC3")
    orders = tuple(range(1, 8))

    capacity_data = {
        "DC1": params["capacity_DC1"],
        "DC2": params["capacity_DC2"],
        "DC3": params["capacity_DC3"],
    }
    storage_rows = {
        "DC1": params["storage_DC1"],
        "DC2": params["storage_DC2"],
        "DC3": params["storage_DC3"],
    }
    cost_rows = {
        "DC1": params["cost_DC1"],
        "DC2": params["cost_DC2"],
        "DC3": params["cost_DC3"],
    }

    model = pyo.ConcreteModel()
    model.centers = pyo.Set(initialize=centers, ordered=True)
    model.orders = pyo.Set(initialize=orders, ordered=True)

    model.capacity = pyo.Param(
        model.centers,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.storage = pyo.Param(
        model.centers,
        model.orders,
        initialize={
            (center, order): storage_rows[center][order - 1]
            for center in centers
            for order in orders
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.centers,
        model.orders,
        initialize={
            (center, order): cost_rows[center][order - 1]
            for center in centers
            for order in orders
        },
        within=pyo.Reals,
    )

    # The solved binary variables explicitly identify each order's center.
    model.assignment = pyo.Var(
        model.centers,
        model.orders,
        domain=pyo.Binary,
    )

    def assign_once_rule(instance, order):
        return sum(
            instance.assignment[center, order]
            for center in instance.centers
        ) == 1

    model.assign_once = pyo.Constraint(
        model.orders,
        rule=assign_once_rule,
    )

    def storage_limit_rule(instance, center):
        return sum(
            instance.storage[center, order]
            * instance.assignment[center, order]
            for order in instance.orders
        ) <= instance.capacity[center]

    model.storage_limit = pyo.Constraint(
        model.centers,
        rule=storage_limit_rule,
    )

    model.total_shipping_cost = pyo.Objective(
        expr=sum(
            model.cost[center, order] * model.assignment[center, order]
            for center in model.centers
            for order in model.orders
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_shipping_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}