# IR {
#   "sets": {"products": [0, 1, 2], "months": [1, 2, 3, 4, 5, 6]},
#   "params": {"demand": "product-month matrix", "production_cost": "product-month matrix", "setup_cost": "product-month matrix", "holding_cost": "product vector", "capacity": "month vector", "capacity_consumption": "product vector"},
#   "variables": {"production[p,t]": "nonnegative continuous", "inventory[p,t]": "nonnegative continuous", "setup[p,t]": "binary"},
#   "constraints": [
#     "For each p,t: sum(production[p,k] for k <= t) = sum(demand[p,k] for k <= t) + inventory[p,t].",
#     "For each t: sum(capacity_consumption[p] * production[p,t] for p) <= capacity[t].",
#     "For each p,t: production[p,t] <= sum(demand[p,k] for k >= t) * setup[p,t]."
#   ],
#   "objective": "Minimize sum(production_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + holding_cost[p]*inventory[p,t] for p,t)."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using matrices with product rows and zero-based month columns."""
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.months = pyo.RangeSet(1, 6)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: demand[product][month - 1],
    )
    model.production_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: production_cost[product][month - 1],
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: setup_cost[product][month - 1],
    )
    model.holding_cost = pyo.Param(
        model.products,
        initialize=lambda mdl, product: holding_cost[product],
    )
    model.capacity = pyo.Param(
        model.months,
        initialize=lambda mdl, month: capacity[month - 1],
    )
    model.capacity_consumption = pyo.Param(
        model.products,
        initialize=lambda mdl, product: capacity_consumption[product],
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(model.products, model.months, domain=pyo.Binary)

    def inventory_balance_rule(mdl, product, month):
        return (
            sum(
                mdl.production[product, period]
                for period in mdl.months
                if period <= month
            )
            == sum(
                mdl.demand[product, period]
                for period in mdl.months
                if period <= month
            )
            + mdl.inventory[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def capacity_limit_rule(mdl, month):
        return (
            sum(
                mdl.capacity_consumption[product] * mdl.production[product, month]
                for product in mdl.products
            )
            <= mdl.capacity[month]
        )

    model.capacity_limit = pyo.Constraint(
        model.months, rule=capacity_limit_rule
    )

    def setup_link_rule(mdl, product, month):
        return mdl.production[product, month] <= (
            sum(
                mdl.demand[product, period]
                for period in mdl.months
                if period >= month
            )
            * mdl.setup[product, month]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.months, rule=setup_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, month]
            * model.production[product, month]
            + model.setup_cost[product, month] * model.setup[product, month]
            + model.holding_cost[product] * model.inventory[product, month]
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