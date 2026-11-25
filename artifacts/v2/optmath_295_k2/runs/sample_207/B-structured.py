# IR: {"sets":{"P":["A","B"],"T":[1,2,3,4,5,6,7],"S":[0,1,2,3,4,5,6,7]},"params":{"demand_A":"T","demand_B":"T","prod_cost_A":"T","prod_cost_B":"T","setup_cost_A":"T","setup_cost_B":"T","hold_cost_A":"T","hold_cost_B":"T","capacity":"T","resource_use_A":"scalar","resource_use_B":"scalar","max_prod_A":"T","max_prod_B":"T"},"variables":{"production[P,T]":"nonnegative continuous","inventory[P,S]":"nonnegative continuous","setup[P,T]":"binary"},"constraints":["inventory[p,0] = 0 for p in P (assumed zero initial inventory)","inventory[p,t-1] + production[p,t] = demand[p,t] + inventory[p,t] for p in P,t in T","production[p,t] <= max_prod[p,t]*setup[p,t] for p in P,t in T","sum(resource_use[p]*production[p,t] for p in P) <= capacity[t] for t in T"],"objective":"minimize sum(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost[p,t]*inventory[p,t] for p in P,t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the seven-week production and inventory planning problem.

    Weekly inputs must be either seven-element sequences ordered by week,
    or mappings with integer keys 1 through 7. Initial inventory is assumed
    to be zero. Final inventory is constrained only to be nonnegative.
    Production and inventory quantities are continuous.
    """

    def weekly_value(data, week):
        return data[week] if isinstance(data, Mapping) else data[week - 1]

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
    capacity_data = params["capacity"]
    resource_use_data = {
        "A": params["resource_use_A"],
        "B": params["resource_use_B"],
    }
    production_limit_data = {
        "A": params["max_prod_A"],
        "B": params["max_prod_B"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=("A", "B"), ordered=True)
    model.weeks = pyo.RangeSet(1, 7)
    model.inventory_periods = pyo.RangeSet(0, 7)

    def indexed_weekly_data(source):
        return {
            (product, week): weekly_value(source[product], week)
            for product in model.products
            for week in model.weeks
        }

    model.demand = pyo.Param(
        model.products,
        model.weeks,
        initialize=indexed_weekly_data(demand_data),
        within=pyo.NonNegativeReals,
    )
    model.production_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=indexed_weekly_data(production_cost_data),
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=indexed_weekly_data(setup_cost_data),
        within=pyo.NonNegativeReals,
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=indexed_weekly_data(holding_cost_data),
        within=pyo.Reals,
    )
    model.weekly_capacity = pyo.Param(
        model.weeks,
        initialize={
            week: weekly_value(capacity_data, week)
            for week in model.weeks
        },
        within=pyo.NonNegativeReals,
    )
    model.resource_use = pyo.Param(
        model.products,
        initialize=resource_use_data,
        within=pyo.PositiveReals,
    )
    model.production_limit = pyo.Param(
        model.products,
        model.weeks,
        initialize=indexed_weekly_data(production_limit_data),
        within=pyo.NonNegativeReals,
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

    def initial_inventory_rule(instance, product):
        return instance.inventory[product, 0] == 0

    model.initial_inventory = pyo.Constraint(
        model.products, rule=initial_inventory_rule
    )

    def inventory_balance_rule(instance, product, week):
        return (
            instance.inventory[product, week - 1]
            + instance.production[product, week]
            == instance.demand[product, week]
            + instance.inventory[product, week]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.weeks, rule=inventory_balance_rule
    )

    def setup_link_rule(instance, product, week):
        return (
            instance.production[product, week]
            <= instance.production_limit[product, week]
            * instance.setup[product, week]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.weeks, rule=setup_link_rule
    )

    def resource_capacity_rule(instance, week):
        return (
            sum(
                instance.resource_use[product]
                * instance.production[product, week]
                for product in instance.products
            )
            <= instance.weekly_capacity[week]
        )

    model.resource_capacity = pyo.Constraint(
        model.weeks, rule=resource_capacity_rule
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

    # Appsi can raise RuntimeError when no feasible solution can be loaded.
    # Leave variables uninitialized and let objective retrieval decide success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}