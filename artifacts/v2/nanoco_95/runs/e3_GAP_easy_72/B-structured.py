# IR: {"sets":{"centers":["DC1","DC2","DC3"],"orders":[1,2,3,4,5,6,7]},"params":{"capacity_DC1":"scalar","capacity_DC2":"scalar","capacity_DC3":"scalar","space_DC1":"length-7 sequence in order-number order","space_DC2":"length-7 sequence in order-number order","space_DC3":"length-7 sequence in order-number order","cost_DC1":"length-7 sequence in order-number order","cost_DC2":"length-7 sequence in order-number order","cost_DC3":"length-7 sequence in order-number order"},"variables":{"assignment[center,order]":"binary; 1 assigns the order to the center"},"constraints":["For each order: sum(assignment[center,order] over centers) = 1","For each center: sum(space[center,order]*assignment[center,order] over orders) <= capacity[center]"],"objective":"minimize sum(cost[center,order]*assignment[center,order] over centers and orders)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the allocation problem; sequence entries correspond to orders 1–7."""
    centers = ("DC1", "DC2", "DC3")
    orders = range(1, 8)

    capacities = {
        "DC1": params["capacity_DC1"],
        "DC2": params["capacity_DC2"],
        "DC3": params["capacity_DC3"],
    }
    spaces = {
        "DC1": params["space_DC1"],
        "DC2": params["space_DC2"],
        "DC3": params["space_DC3"],
    }
    costs = {
        "DC1": params["cost_DC1"],
        "DC2": params["cost_DC2"],
        "DC3": params["cost_DC3"],
    }

    model = pyo.ConcreteModel()
    model.centers = pyo.Set(initialize=centers, ordered=True)
    model.orders = pyo.Set(initialize=orders, ordered=True)

    model.capacity = pyo.Param(
        model.centers,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.space = pyo.Param(
        model.centers,
        model.orders,
        initialize={
            (center, order): spaces[center][order - 1]
            for center in centers
            for order in orders
        },
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.centers,
        model.orders,
        initialize={
            (center, order): costs[center][order - 1]
            for center in centers
            for order in orders
        },
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.centers, model.orders, domain=pyo.Binary
    )

    def assign_once_rule(instance, order):
        return sum(
            instance.assignment[center, order]
            for center in instance.centers
        ) == 1

    model.assign_once = pyo.Constraint(
        model.orders, rule=assign_once_rule
    )

    def capacity_rule(instance, center):
        return sum(
            instance.space[center, order]
            * instance.assignment[center, order]
            for order in instance.orders
        ) <= instance.capacity[center]

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_shipping_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[center, order]
            * model.assignment[center, order]
            for center in model.centers
            for order in model.orders
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_shipping_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}