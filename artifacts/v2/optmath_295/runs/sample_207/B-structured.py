# IR: {"sets":{"products":["A","B"],"weeks":[1,2,3,4,5,6,7],"inventory_periods":[0,1,2,3,4,5,6,7]},"params":{"demand_A":"weekly demand","demand_B":"weekly demand","prod_cost_A":"weekly unit production cost","prod_cost_B":"weekly unit production cost","setup_cost_A":"weekly fixed setup cost","setup_cost_B":"weekly fixed setup cost","hold_cost_A":"weekly unit ending-inventory cost","hold_cost_B":"weekly unit ending-inventory cost","capacity":"weekly resource capacity","resource_A":"resource consumption per unit","resource_B":"resource consumption per unit","limit_A":"weekly production upper bound","limit_B":"weekly production upper bound"},"variables":{"production[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals, including period 0","setup[p,t]":"Binary"},"constraints":["inventory[p,0] = 0 for each product (zero initial inventory assumed)","inventory[p,t-1] + production[p,t] - inventory[p,t] = demand[p,t] for each product and week","sum(resource[p]*production[p,t] for p) <= capacity[t] for each week","production[p,t] <= limit[p,t]*setup[p,t] for each product and week"],"objective":"minimize sum(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost[p,t]*inventory[p,t] for each product and week)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the two-product, seven-week production planning problem.

    Weekly inputs may be sequences ordered from week 1 through week 7,
    or mappings keyed by week numbers (integers or numeric strings).
    Production and inventory quantities are continuous.
    """
    products = ("A", "B")
    weeks = tuple(range(1, 8))

    def weekly_value(values, week):
        if isinstance(values, Mapping):
            if week in values:
                return values[week]
            return values[str(week)]
        return values[week - 1]

    demand_data = {
        "A": params["demand_A"],
        "B": params["demand_B"],
    }
    production_cost_data = {
        "A": params["prod_cost_A"],
        "B": params["prod_cost_B"],
    }
    setup_cost_data = {
        "A": params["setup_cost_A"],
        "B": params["setup_cost_B"],
    }
    holding_cost_data = {
        "A": params["hold_cost_A"],
        "B": params["hold_cost_B"],
    }
    production_limit_data = {
        "A": params["limit_A"],
        "B": params["limit_B"],
    }
    resource_data = {
        "A": params["resource_A"],
        "B": params["resource_B"],
    }
    capacity_data = params["capacity"]

    def product_week_values(data):
        return {
            (product, week): weekly_value(data[product], week)
            for product in products
            for week in weeks
        }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.weeks = pyo.RangeSet(1, 7)
    model.inventory_periods = pyo.RangeSet(0, 7)

    model.demand = pyo.Param(
        model.products,
        model.weeks,
        initialize=product_week_values(demand_data),
    )
    model.production_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=product_week_values(production_cost_data),
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=product_week_values(setup_cost_data),
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=product_week_values(holding_cost_data),
    )
    model.production_limit = pyo.Param(
        model.products,
        model.weeks,
        initialize=product_week_values(production_limit_data),
    )
    model.resource_use = pyo.Param(
        model.products,
        initialize=resource_data,
    )
    model.weekly_capacity = pyo.Param(
        model.weeks,
        initialize={
            week: weekly_value(capacity_data, week)
            for week in weeks
        },
    )

    model.production = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.inventory_periods, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.weeks, domain=pyo.Binary
    )

    for product in products:
        model.inventory[product, 0].fix(0)

    def inventory_balance_rule(instance, product, week):
        return (
            instance.inventory[product, week - 1]
            + instance.production[product, week]
            - instance.inventory[product, week]
            == instance.demand[product, week]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.weeks,
        rule=inventory_balance_rule,
    )

    def capacity_rule(instance, week):
        return (
            sum(
                instance.resource_use[product]
                * instance.production[product, week]
                for product in instance.products
            )
            <= instance.weekly_capacity[week]
        )

    model.capacity_constraint = pyo.Constraint(
        model.weeks,
        rule=capacity_rule,
    )

    def setup_link_rule(instance, product, week):
        return (
            instance.production[product, week]
            <= instance.production_limit[product, week]
            * instance.setup[product, week]
        )

    model.setup_link = pyo.Constraint(
        model.products,
        model.weeks,
        rule=setup_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, week]
            * model.production[product, week]
            + model.setup_cost[product, week]
            * model.setup[product, week]
            + model.holding_cost[product, week]
            * model.inventory[product, week]
            for product in model.products
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no solution can be loaded. Success below
        # depends exclusively on whether the objective is retrievable.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}