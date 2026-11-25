# IR: {"sets":{"products":["A","B"],"periods":[0,1,2,3,4,5,6]},"params":{"demand_A":"cumulative demand by period","demand_B":"cumulative demand by period","prod_cost_A":"production cost by period","prod_cost_B":"production cost by period","setup_cost_A":"setup cost by period","setup_cost_B":"setup cost by period","hold_cost_A":"holding cost by period","hold_cost_B":"holding cost by period","resource_usage_A":"resource per unit","resource_usage_B":"resource per unit","resource_capacity":"capacity by period"},"derived":{"D[p,t]":"cumulative demand","d[p,t]":"D[p,t] - (D[p,t-1] if t>0 else 0)","U[p,t]":"D[p,6] - (D[p,t-1] if t>0 else 0)"},"variables":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","setup[p,t]":"binary"},"constraints":["inventory[p,t] = (inventory[p,t-1] if t>0 else 0) + production[p,t] - d[p,t]","sum(resource_usage[p]*production[p,t] for p in products) <= resource_capacity[t]","production[p,t] <= U[p,t]*setup[p,t]","inventory[p,6] = 0"],"objective":"minimize sum(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost[p,t]*inventory[p,t] for p in products for t in periods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("A", "B")
    periods = range(7)

    cumulative_demand = {
        "A": params["demand_A"],
        "B": params["demand_B"],
    }
    production_cost = {
        "A": params["prod_cost_A"],
        "B": params["prod_cost_B"],
    }
    setup_cost = {
        "A": params["setup_cost_A"],
        "B": params["setup_cost_B"],
    }
    holding_cost = {
        "A": params["hold_cost_A"],
        "B": params["hold_cost_B"],
    }
    resource_usage = {
        "A": params["resource_usage_A"],
        "B": params["resource_usage_B"],
    }
    resource_capacity = params["resource_capacity"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.periods = pyo.RangeSet(0, 6)

    model.cumulative_demand = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): cumulative_demand[product][period]
            for product in products
            for period in periods
        },
        within=pyo.NonNegativeReals,
    )
    model.production_cost = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): production_cost[product][period]
            for product in products
            for period in periods
        },
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): setup_cost[product][period]
            for product in products
            for period in periods
        },
        within=pyo.Reals,
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): holding_cost[product][period]
            for product in products
            for period in periods
        },
        within=pyo.Reals,
    )
    model.resource_usage = pyo.Param(
        model.products,
        initialize=resource_usage,
        within=pyo.NonNegativeReals,
    )
    model.resource_capacity = pyo.Param(
        model.periods,
        initialize={
            period: resource_capacity[period]
            for period in periods
        },
        within=pyo.NonNegativeReals,
    )

    def period_demand_rule(instance, product, period):
        previous_demand = (
            instance.cumulative_demand[product, period - 1]
            if period > 0
            else 0
        )
        return instance.cumulative_demand[product, period] - previous_demand

    model.period_demand = pyo.Expression(
        model.products, model.periods, rule=period_demand_rule
    )

    def production_limit_rule(instance, product, period):
        previous_demand = (
            instance.cumulative_demand[product, period - 1]
            if period > 0
            else 0
        )
        return instance.cumulative_demand[product, 6] - previous_demand

    model.production_limit = pyo.Expression(
        model.products, model.periods, rule=production_limit_rule
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.periods, domain=pyo.Binary
    )

    def inventory_balance_rule(instance, product, period):
        previous_inventory = (
            instance.inventory[product, period - 1]
            if period > 0
            else 0
        )
        return instance.inventory[product, period] == (
            previous_inventory
            + instance.production[product, period]
            - instance.period_demand[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def resource_capacity_rule(instance, period):
        return sum(
            instance.resource_usage[product]
            * instance.production[product, period]
            for product in instance.products
        ) <= instance.resource_capacity[period]

    model.resource_constraints = pyo.Constraint(
        model.periods, rule=resource_capacity_rule
    )

    def setup_link_rule(instance, product, period):
        return instance.production[product, period] <= (
            instance.production_limit[product, period]
            * instance.setup[product, period]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.periods, rule=setup_link_rule
    )

    def terminal_inventory_rule(instance, product):
        return instance.inventory[product, 6] == 0

    model.terminal_inventory = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, period]
            * model.production[product, period]
            + model.setup_cost[product, period]
            * model.setup[product, period]
            + model.holding_cost[product, period]
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}