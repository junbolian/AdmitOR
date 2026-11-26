# IR: {"sets":{"S":["A","B","C"]},"params":["cost_A","cost_B","cost_C","chairs_per_order_A","chairs_per_order_B","chairs_per_order_C","min_chairs","max_chairs","min_B_if_A"],"derived":{"U[s]":"floor(max_chairs/chairs_per_order[s])"},"variables":{"orders[s]":"nonnegative integer","used[s]":"binary"},"constraints":["min_chairs <= sum(chairs_per_order[s]*orders[s]) <= max_chairs","orders[s] <= U[s]*used[s] for s in S","orders[s] >= used[s] for s in S","chairs_per_order[B]*orders[B] >= min_B_if_A*used[A]","used[B] <= used[C]"],"objective":"minimize sum(cost[s]*orders[s])"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    suppliers = ("A", "B", "C")

    cost = {
        "A": params["cost_A"],
        "B": params["cost_B"],
        "C": params["cost_C"],
    }
    chairs_per_order = {
        "A": params["chairs_per_order_A"],
        "B": params["chairs_per_order_B"],
        "C": params["chairs_per_order_C"],
    }
    min_chairs = params["min_chairs"]
    max_chairs = params["max_chairs"]
    min_B_if_A = params["min_B_if_A"]

    if any(chairs_per_order[supplier] <= 0 for supplier in suppliers):
        return {"objective": None, "status": "invalid_order_size"}

    if max_chairs < 0 or min_chairs > max_chairs:
        return {"objective": None, "status": "infeasible"}

    order_upper_bound = {
        supplier: math.floor(max_chairs / chairs_per_order[supplier])
        for supplier in suppliers
    }

    model = pyo.ConcreteModel()
    model.suppliers = pyo.Set(initialize=suppliers, ordered=True)

    model.orders = pyo.Var(model.suppliers, domain=pyo.NonNegativeIntegers)
    model.used = pyo.Var(model.suppliers, domain=pyo.Binary)

    model.chair_limits = pyo.Constraint(
        expr=pyo.inequality(
            min_chairs,
            sum(
                chairs_per_order[supplier] * model.orders[supplier]
                for supplier in model.suppliers
            ),
            max_chairs,
        )
    )

    def usage_upper_rule(mdl, supplier):
        return (
            mdl.orders[supplier]
            <= order_upper_bound[supplier] * mdl.used[supplier]
        )

    model.usage_upper = pyo.Constraint(
        model.suppliers, rule=usage_upper_rule
    )

    def usage_lower_rule(mdl, supplier):
        return mdl.orders[supplier] >= mdl.used[supplier]

    model.usage_lower = pyo.Constraint(
        model.suppliers, rule=usage_lower_rule
    )

    model.a_requires_b = pyo.Constraint(
        expr=(
            chairs_per_order["B"] * model.orders["B"]
            >= min_B_if_A * model.used["A"]
        )
    )
    model.b_requires_c = pyo.Constraint(
        expr=model.used["B"] <= model.used["C"]
    )

    # Costs are per order, as specified by the PARAMS definitions.
    model.total_cost = pyo.Objective(
        expr=sum(
            cost[supplier] * model.orders[supplier]
            for supplier in model.suppliers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}