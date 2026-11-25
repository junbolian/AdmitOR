# IR: {"sets":{"centers":["DC1","DC2","DC3"],"orders":[1,2,3,4,5,6,7]},"params":{"capacity[dc]":"params['capacity_'+dc]","storage[dc,order]":"params['storage_'+dc][order-1]","cost[dc,order]":"params['cost_'+dc][order-1]"},"variables":{"assignment[dc,order]":"Binary; 1 iff order is assigned to dc"},"constraints":["For each order: sum(dc, assignment[dc,order]) == 1","For each dc: sum(order, storage[dc,order]*assignment[dc,order]) <= capacity[dc]"],"objective":"minimize sum(dc,order, cost[dc,order]*assignment[dc,order])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the allocation problem; storage and cost inputs are length-7 sequences."""
    centers = ("DC1", "DC2", "DC3")
    orders = range(1, 8)

    capacities = {
        center: params["capacity_" + center]
        for center in centers
    }
    storage = {
        (center, order): params["storage_" + center][order - 1]
        for center in centers
        for order in orders
    }
    costs = {
        (center, order): params["cost_" + center][order - 1]
        for center in centers
        for order in orders
    }

    model = pyo.ConcreteModel()
    model.centers = pyo.Set(initialize=centers, ordered=True)
    model.orders = pyo.Set(initialize=orders, ordered=True)

    model.capacity = pyo.Param(model.centers, initialize=capacities)
    model.storage = pyo.Param(
        model.centers, model.orders, initialize=storage
    )
    model.shipping_cost = pyo.Param(
        model.centers, model.orders, initialize=costs
    )

    model.assignment = pyo.Var(
        model.centers, model.orders, domain=pyo.Binary
    )

    def assignment_rule(instance, order):
        return sum(
            instance.assignment[center, order]
            for center in instance.centers
        ) == 1

    model.order_assignment = pyo.Constraint(
        model.orders, rule=assignment_rule
    )

    def capacity_rule(instance, center):
        return sum(
            instance.storage[center, order]
            * instance.assignment[center, order]
            for order in instance.orders
        ) <= instance.capacity[center]

    model.storage_limit = pyo.Constraint(
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}