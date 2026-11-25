# IR: {"sets":{"products":["A","B"],"weeks":[1,2,3,4,5,6,7]},"params":{"demand_A":"weekly","demand_B":"weekly","prod_cost_A":"weekly","prod_cost_B":"weekly","setup_cost_A":"weekly","setup_cost_B":"weekly","hold_cost_A":"weekly","hold_cost_B":"weekly","capacity":"weekly","resource_use_A":"scalar","resource_use_B":"scalar","max_prod_A":"weekly","max_prod_B":"weekly"},"variables":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous, end of week","setup[p,t]":"binary"},"constraints":["production[p,1] - inventory[p,1] = demand[p,1] (zero initial inventory)","inventory[p,t-1] + production[p,t] - inventory[p,t] = demand[p,t] for t=2,...,7","sum_p resource_use[p]*production[p,t] <= capacity[t] for each t","production[p,t] <= max_prod[p,t]*setup[p,t] for each p,t"],"objective":"minimize sum_{p,t}(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost[p,t]*inventory[p,t])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Weekly inputs accept seven-element sequences in chronological order,
    or mappings keyed by week numbers 1 through 7 (integers or strings).

    Initial inventory is zero. Ending inventory is nonnegative.
    Production and inventory quantities are continuous.
    """

    def weekly_values(values):
        if isinstance(values, Mapping):
            return {
                week: values[week] if week in values else values[str(week)]
                for week in range(1, 8)
            }
        if len(values) != 7:
            raise ValueError("Weekly inputs must contain exactly seven values.")
        return {week: values[week - 1] for week in range(1, 8)}

    demand_data = {
        "A": weekly_values(params["demand_A"]),
        "B": weekly_values(params["demand_B"]),
    }
    production_cost_data = {
        "A": weekly_values(params["prod_cost_A"]),
        "B": weekly_values(params["prod_cost_B"]),
    }
    setup_cost_data = {
        "A": weekly_values(params["setup_cost_A"]),
        "B": weekly_values(params["setup_cost_B"]),
    }
    holding_cost_data = {
        "A": weekly_values(params["hold_cost_A"]),
        "B": weekly_values(params["hold_cost_B"]),
    }
    capacity_data = weekly_values(params["capacity"])
    resource_use_data = {
        "A": params["resource_use_A"],
        "B": params["resource_use_B"],
    }
    maximum_production_data = {
        "A": weekly_values(params["max_prod_A"]),
        "B": weekly_values(params["max_prod_B"]),
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.weeks = pyo.RangeSet(1, 7)

    model.demand = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: demand_data[product][week],
        within=pyo.NonNegativeReals,
    )
    model.production_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: production_cost_data[product][week],
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: setup_cost_data[product][week],
        within=pyo.NonNegativeReals,
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: holding_cost_data[product][week],
        within=pyo.Reals,
    )
    model.weekly_capacity = pyo.Param(
        model.weeks,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.resource_use = pyo.Param(
        model.products,
        initialize=resource_use_data,
        within=pyo.NonNegativeReals,
    )
    model.maximum_production = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: maximum_production_data[product][week],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(model.products, model.weeks, domain=pyo.Binary)

    def inventory_balance_rule(mdl, product, week):
        previous_inventory = (
            0 if week == 1 else mdl.inventory[product, week - 1]
        )
        return (
            previous_inventory
            + mdl.production[product, week]
            - mdl.inventory[product, week]
            == mdl.demand[product, week]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.weeks, rule=inventory_balance_rule
    )

    def resource_capacity_rule(mdl, week):
        return (
            sum(
                mdl.resource_use[product] * mdl.production[product, week]
                for product in mdl.products
            )
            <= mdl.weekly_capacity[week]
        )

    model.resource_capacity = pyo.Constraint(
        model.weeks, rule=resource_capacity_rule
    )

    def setup_link_rule(mdl, product, week):
        return (
            mdl.production[product, week]
            <= mdl.maximum_production[product, week] * mdl.setup[product, week]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.weeks, rule=setup_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, week] * model.production[product, week]
            + model.setup_cost[product, week] * model.setup[product, week]
            + model.holding_cost[product, week] * model.inventory[product, week]
            for product in model.products
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPSI raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions still propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}