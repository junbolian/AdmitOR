# {
#   "sets": {"P": ["A", "B"], "T": [0, 1, 2, 3, 4, 5]},
#   "params": {
#     "cumulative_demand_A": "Cumulative demand for A, indexed by T",
#     "cumulative_demand_B": "Cumulative demand for B, indexed by T",
#     "production_cost_A": "Unit production cost for A, indexed by T",
#     "production_cost_B": "Unit production cost for B, indexed by T",
#     "setup_cost_A": "Setup cost for A, indexed by T",
#     "setup_cost_B": "Setup cost for B, indexed by T",
#     "holding_cost_A": "Unit ending-inventory cost for A, indexed by T",
#     "holding_cost_B": "Unit ending-inventory cost for B, indexed by T",
#     "resource_usage_A": "Resource consumed per unit of A",
#     "resource_usage_B": "Resource consumed per unit of B",
#     "resource_capacity": "Shared resource capacity, indexed by T"
#   },
#   "derived": {
#     "D[p,t]": "cumulative_demand_p[t]",
#     "d[p,t]": "D[p,t] - (D[p,t-1] if t>0 else 0)",
#     "U[p,t]": "D[p,5] - (D[p,t-1] if t>0 else 0)"
#   },
#   "variables": {
#     "production[p,t]": "NonNegativeReals",
#     "inventory[p,t]": "NonNegativeReals",
#     "setup[p,t]": "Binary"
#   },
#   "constraints": [
#     "inventory[p,t] = (inventory[p,t-1] if t>0 else 0) + production[p,t] - d[p,t], for all p,t",
#     "production[p,t] <= U[p,t] * setup[p,t], for all p,t",
#     "sum(p in P, resource_usage_p * production[p,t]) <= resource_capacity[t], for all t",
#     "inventory[p,5] = 0, for all p"
#   ],
#   "objective": "min sum(p,t, production_cost_p[t]*production[p,t] + setup_cost_p[t]*setup[p,t] + holding_cost_p[t]*inventory[p,t])"
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the six-month capacitated production and inventory problem.

    Monthly inputs may be sequences ordered M0 through M5, or mappings
    keyed by integers 0 through 5 or strings "M0" through "M5".
    Production and inventory quantities are continuous.
    """

    products = ("A", "B")
    months = tuple(range(6))

    def monthly_values(values):
        if isinstance(values, Mapping):
            return {
                month: float(
                    values[month] if month in values else values[f"M{month}"]
                )
                for month in months
            }
        return {month: float(values[month]) for month in months}

    cumulative_demand = {
        "A": monthly_values(params["cumulative_demand_A"]),
        "B": monthly_values(params["cumulative_demand_B"]),
    }
    production_cost = {
        "A": monthly_values(params["production_cost_A"]),
        "B": monthly_values(params["production_cost_B"]),
    }
    setup_cost = {
        "A": monthly_values(params["setup_cost_A"]),
        "B": monthly_values(params["setup_cost_B"]),
    }
    holding_cost = {
        "A": monthly_values(params["holding_cost_A"]),
        "B": monthly_values(params["holding_cost_B"]),
    }
    resource_usage = {
        "A": float(params["resource_usage_A"]),
        "B": float(params["resource_usage_B"]),
    }
    resource_capacity = monthly_values(params["resource_capacity"])

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.months = pyo.Set(initialize=months, ordered=True)

    model.cumulative_demand = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: cumulative_demand[product][month],
    )
    model.production_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: production_cost[product][month],
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: setup_cost[product][month],
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: holding_cost[product][month],
    )
    model.resource_usage = pyo.Param(
        model.products, initialize=resource_usage
    )
    model.resource_capacity = pyo.Param(
        model.months, initialize=resource_capacity
    )

    def demand_rule(mdl, product, month):
        previous = (
            mdl.cumulative_demand[product, month - 1] if month > 0 else 0
        )
        return mdl.cumulative_demand[product, month] - previous

    def remaining_demand_rule(mdl, product, month):
        previous = (
            mdl.cumulative_demand[product, month - 1] if month > 0 else 0
        )
        return mdl.cumulative_demand[product, months[-1]] - previous

    model.monthly_demand = pyo.Param(
        model.products, model.months, initialize=demand_rule
    )
    model.remaining_demand = pyo.Param(
        model.products, model.months, initialize=remaining_demand_rule
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.months, domain=pyo.Binary
    )

    def inventory_balance_rule(mdl, product, month):
        previous_inventory = (
            mdl.inventory[product, month - 1] if month > 0 else 0
        )
        return mdl.inventory[product, month] == (
            previous_inventory
            + mdl.production[product, month]
            - mdl.monthly_demand[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def setup_link_rule(mdl, product, month):
        return mdl.production[product, month] <= (
            mdl.remaining_demand[product, month] * mdl.setup[product, month]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.months, rule=setup_link_rule
    )

    def resource_limit_rule(mdl, month):
        return sum(
            mdl.resource_usage[product] * mdl.production[product, month]
            for product in mdl.products
        ) <= mdl.resource_capacity[month]

    model.resource_limit = pyo.Constraint(
        model.months, rule=resource_limit_rule
    )

    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: mdl.inventory[product, months[-1]] == 0,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, month]
            * model.production[product, month]
            + model.setup_cost[product, month]
            * model.setup[product, month]
            + model.holding_cost[product, month]
            * model.inventory[product, month]
            for product in model.products
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}