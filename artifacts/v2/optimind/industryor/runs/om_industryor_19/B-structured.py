# IR: {"sets":{"S":["A","B","C"],"L":["A","B"]},"params":{"cost":{"A":"params['cost_A']","B":"params['cost_B']","C":"params['cost_C']"},"tables_per_order":{"A":"params['tables_per_order_A']","B":"params['tables_per_order_B']","C":"params['tables_per_order_C']"},"min_tables":"params['min_tables']","max_tables":"params['max_tables']","min_tables_B_if_A":"params['min_tables_B_if_A']","order_cap[s]":"max(0,floor(max_tables/tables_per_order[s]))"},"variables":{"orders[s in S]":"nonnegative integer","used[s in L]":"binary"},"constraints":["sum(tables_per_order[s]*orders[s] for s in S) >= min_tables","sum(tables_per_order[s]*orders[s] for s in S) <= max_tables","orders[s] <= order_cap[s]*used[s] for s in L","orders[s] >= used[s] for s in L","tables_per_order['B']*orders['B'] >= min_tables_B_if_A*used['A']","orders['C'] >= used['B']"],"objective":"minimize sum(cost[s]*tables_per_order[s]*orders[s] for s in S)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.suppliers = pyo.Set(initialize=["A", "B", "C"], ordered=True)
    model.linked_suppliers = pyo.Set(initialize=["A", "B"], ordered=True)

    model.table_cost = pyo.Param(
        model.suppliers,
        initialize={
            "A": params["cost_A"],
            "B": params["cost_B"],
            "C": params["cost_C"],
        },
        within=pyo.Reals,
    )
    model.tables_per_order = pyo.Param(
        model.suppliers,
        initialize={
            "A": params["tables_per_order_A"],
            "B": params["tables_per_order_B"],
            "C": params["tables_per_order_C"],
        },
        within=pyo.PositiveReals,
    )
    model.minimum_tables = pyo.Param(
        initialize=params["min_tables"], within=pyo.Reals
    )
    model.maximum_tables = pyo.Param(
        initialize=params["max_tables"], within=pyo.Reals
    )
    model.required_B_tables = pyo.Param(
        initialize=params["min_tables_B_if_A"], within=pyo.NonNegativeReals
    )

    def order_cap_rule(current_model, supplier):
        return max(
            0,
            math.floor(
                pyo.value(current_model.maximum_tables)
                / pyo.value(current_model.tables_per_order[supplier])
            ),
        )

    model.order_cap = pyo.Param(
        model.suppliers,
        initialize=order_cap_rule,
        within=pyo.NonNegativeIntegers,
    )

    model.orders = pyo.Var(model.suppliers, domain=pyo.NonNegativeIntegers)
    model.used = pyo.Var(model.linked_suppliers, domain=pyo.Binary)

    model.total_tables = pyo.Expression(
        expr=sum(
            model.tables_per_order[supplier] * model.orders[supplier]
            for supplier in model.suppliers
        )
    )

    model.minimum_requirement = pyo.Constraint(
        expr=model.total_tables >= model.minimum_tables
    )
    model.maximum_requirement = pyo.Constraint(
        expr=model.total_tables <= model.maximum_tables
    )

    def activation_upper_rule(current_model, supplier):
        return (
            current_model.orders[supplier]
            <= current_model.order_cap[supplier] * current_model.used[supplier]
        )

    def activation_lower_rule(current_model, supplier):
        return current_model.orders[supplier] >= current_model.used[supplier]

    model.activation_upper = pyo.Constraint(
        model.linked_suppliers, rule=activation_upper_rule
    )
    model.activation_lower = pyo.Constraint(
        model.linked_suppliers, rule=activation_lower_rule
    )
    model.A_requires_B = pyo.Constraint(
        expr=model.tables_per_order["B"] * model.orders["B"]
        >= model.required_B_tables * model.used["A"]
    )
    model.B_requires_C = pyo.Constraint(
        expr=model.orders["C"] >= model.used["B"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.table_cost[supplier]
            * model.tables_per_order[supplier]
            * model.orders[supplier]
            for supplier in model.suppliers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}