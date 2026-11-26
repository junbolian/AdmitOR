# IR: {"sets":{"S":["A","B","C"],"T":["A","B"]},"params":["cost_A","cost_B","cost_C","tables_per_order_A","tables_per_order_B","tables_per_order_C","min_tables","max_tables","min_tables_B_if_A"],"decision_variables":{"orders[s in S]":"nonnegative integer","used[s in T]":"binary"},"derived":{"U[s]":"floor(max_tables / tables_per_order_s)"},"constraints":["sum(tables_per_order_s * orders[s] for s in S) >= min_tables","sum(tables_per_order_s * orders[s] for s in S) <= max_tables","orders[s] <= U[s] * used[s] for s in T","orders[s] >= used[s] for s in T","tables_per_order_B * orders[B] >= min_tables_B_if_A * used[A]","orders[C] >= used[B]"],"objective":"minimize sum(cost_s * tables_per_order_s * orders[s] for s in S)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    suppliers = ("A", "B", "C")
    trigger_suppliers = ("A", "B")

    costs = {
        "A": params["cost_A"],
        "B": params["cost_B"],
        "C": params["cost_C"],
    }
    tables_per_order = {
        "A": params["tables_per_order_A"],
        "B": params["tables_per_order_B"],
        "C": params["tables_per_order_C"],
    }
    minimum_tables = params["min_tables"]
    maximum_tables = params["max_tables"]
    minimum_b_if_a = params["min_tables_B_if_A"]

    upper_orders = {
        supplier: math.floor(maximum_tables / tables_per_order[supplier])
        for supplier in suppliers
    }

    model = pyo.ConcreteModel()
    model.suppliers = pyo.Set(initialize=suppliers, ordered=True)
    model.trigger_suppliers = pyo.Set(
        initialize=trigger_suppliers, ordered=True
    )

    model.unit_cost = pyo.Param(model.suppliers, initialize=costs)
    model.order_size = pyo.Param(
        model.suppliers, initialize=tables_per_order
    )
    model.minimum_tables = pyo.Param(initialize=minimum_tables)
    model.maximum_tables = pyo.Param(initialize=maximum_tables)
    model.minimum_b_if_a = pyo.Param(initialize=minimum_b_if_a)
    model.upper_orders = pyo.Param(
        model.suppliers, initialize=upper_orders
    )

    model.orders = pyo.Var(
        model.suppliers, domain=pyo.NonNegativeIntegers
    )
    model.used = pyo.Var(model.trigger_suppliers, domain=pyo.Binary)

    model.total_tables = pyo.Expression(
        expr=sum(
            model.order_size[supplier] * model.orders[supplier]
            for supplier in model.suppliers
        )
    )

    model.minimum_requirement = pyo.Constraint(
        expr=model.total_tables >= model.minimum_tables
    )
    model.maximum_requirement = pyo.Constraint(
        expr=model.total_tables <= model.maximum_tables
    )

    def activation_upper_rule(instance, supplier):
        return (
            instance.orders[supplier]
            <= instance.upper_orders[supplier] * instance.used[supplier]
        )

    model.activation_upper = pyo.Constraint(
        model.trigger_suppliers, rule=activation_upper_rule
    )

    def activation_lower_rule(instance, supplier):
        return instance.orders[supplier] >= instance.used[supplier]

    model.activation_lower = pyo.Constraint(
        model.trigger_suppliers, rule=activation_lower_rule
    )

    model.a_requires_b = pyo.Constraint(
        expr=(
            model.order_size["B"] * model.orders["B"]
            >= model.minimum_b_if_a * model.used["A"]
        )
    )
    model.b_requires_c = pyo.Constraint(
        expr=model.orders["C"] >= model.used["B"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[supplier]
            * model.order_size[supplier]
            * model.orders[supplier]
            for supplier in model.suppliers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its default solution loading finds no
        # feasible solution. Still determine success by objective retrieval.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}