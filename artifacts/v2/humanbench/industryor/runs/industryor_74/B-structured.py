# IR: {"sets":{"manufacturers":["A","B","C"],"linked":["A","B"]},"params":{"cost":{"A":"cost_A","B":"cost_B","C":"cost_C"},"capacity":{"A":"capacity_A","B":"capacity_B","C":"capacity_C"},"minimum":"min_chairs","maximum":"max_chairs","minimum_B_if_A":"min_B_if_A"},"derived":{"upper[i]":"max(0,floor(maximum/capacity[i]))"},"variables":{"orders[i]":"nonnegative integer, <= upper[i]","chosen[i in linked]":"binary"},"constraints":["sum(capacity[i]*orders[i]) >= minimum","sum(capacity[i]*orders[i]) <= maximum","orders[i] <= upper[i]*chosen[i] for i in linked","orders[i] >= chosen[i] for i in linked","capacity[B]*orders[B] >= minimum_B_if_A*chosen[A]","orders[C] >= chosen[B]"],"objective":"minimize sum(cost[i]*capacity[i]*orders[i])"}

from math import floor

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    manufacturers = ("A", "B", "C")
    linked = ("A", "B")

    costs = {
        "A": params["cost_A"],
        "B": params["cost_B"],
        "C": params["cost_C"],
    }
    capacities = {
        "A": params["capacity_A"],
        "B": params["capacity_B"],
        "C": params["capacity_C"],
    }
    minimum = params["min_chairs"]
    maximum = params["max_chairs"]
    minimum_B_if_A = params["min_B_if_A"]

    if any(capacities[supplier] <= 0 for supplier in manufacturers):
        return {"objective": None, "status": "invalid_capacity"}

    upper = {
        supplier: max(0, floor(maximum / capacities[supplier]))
        for supplier in manufacturers
    }

    model = pyo.ConcreteModel()
    model.manufacturers = pyo.Set(initialize=manufacturers, ordered=True)
    model.linked = pyo.Set(initialize=linked, ordered=True)

    model.unit_cost = pyo.Param(model.manufacturers, initialize=costs)
    model.batch_size = pyo.Param(model.manufacturers, initialize=capacities)
    model.minimum_chairs = pyo.Param(initialize=minimum)
    model.maximum_chairs = pyo.Param(initialize=maximum)
    model.required_B = pyo.Param(initialize=minimum_B_if_A)
    model.order_upper = pyo.Param(model.manufacturers, initialize=upper)

    def order_bounds(instance, supplier):
        return 0, upper[supplier]

    model.orders = pyo.Var(
        model.manufacturers,
        domain=pyo.NonNegativeIntegers,
        bounds=order_bounds,
    )
    model.chosen = pyo.Var(model.linked, domain=pyo.Binary)

    model.total_chairs = pyo.Expression(
        expr=sum(
            model.batch_size[supplier] * model.orders[supplier]
            for supplier in model.manufacturers
        )
    )

    model.minimum_requirement = pyo.Constraint(
        expr=model.total_chairs >= model.minimum_chairs
    )
    model.maximum_requirement = pyo.Constraint(
        expr=model.total_chairs <= model.maximum_chairs
    )

    def selection_upper_rule(instance, supplier):
        return (
            instance.orders[supplier]
            <= instance.order_upper[supplier] * instance.chosen[supplier]
        )

    def selection_lower_rule(instance, supplier):
        return instance.orders[supplier] >= instance.chosen[supplier]

    model.selection_upper = pyo.Constraint(
        model.linked, rule=selection_upper_rule
    )
    model.selection_lower = pyo.Constraint(
        model.linked, rule=selection_lower_rule
    )

    model.A_requires_B = pyo.Constraint(
        expr=(
            model.batch_size["B"] * model.orders["B"]
            >= model.required_B * model.chosen["A"]
        )
    )
    model.B_requires_C = pyo.Constraint(
        expr=model.orders["C"] >= model.chosen["B"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[supplier]
            * model.batch_size[supplier]
            * model.orders[supplier]
            for supplier in model.manufacturers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi HiGHS raises RuntimeError when no solution can be loaded.
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}