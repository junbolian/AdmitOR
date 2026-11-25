# IR: {"sets":{"item_set":["A","B"],"period_set":[0,1,2,3]},"params":{"demand_A":"period-indexed","demand_B":"period-indexed","prod_cost_A":"period-indexed","prod_cost_B":"period-indexed","setup_cost_A":"period-indexed","setup_cost_B":"period-indexed","hold_cost_A":"period-indexed","hold_cost_B":"period-indexed","capacity":"period-indexed","usage_A":"scalar","usage_B":"scalar","prod_ub_A":"period-indexed","prod_ub_B":"period-indexed"},"variables":{"production[item,t]":"nonnegative continuous","inventory[item,t]":"nonnegative continuous","setup[item,t]":"binary"},"constraints":["inventory[item,t] = (0 if t=0 else inventory[item,t-1]) + production[item,t] - demand[item,t]","sum(usage[item]*production[item,t] for item in item_set) <= capacity[t]","production[item,t] <= prod_ub[item,t]*setup[item,t]"],"objective":"minimize sum(prod_cost[item,t]*production[item,t] + setup_cost[item,t]*setup[item,t] + hold_cost[item,t]*inventory[item,t] for item in item_set for t in period_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept period-indexed sequences or mappings and scalar resource usage."""
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
    usage_data = {
        "A": params["usage_A"],
        "B": params["usage_B"],
    }
    production_bound_data = {
        "A": params["prod_ub_A"],
        "B": params["prod_ub_B"],
    }

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=("A", "B"), ordered=True)
    model.period_set = pyo.RangeSet(0, 3)

    model.demand = pyo.Param(
        model.item_set,
        model.period_set,
        initialize=lambda mdl, item, period: demand_data[item][period],
    )
    model.production_cost = pyo.Param(
        model.item_set,
        model.period_set,
        initialize=lambda mdl, item, period: production_cost_data[item][period],
    )
    model.setup_cost = pyo.Param(
        model.item_set,
        model.period_set,
        initialize=lambda mdl, item, period: setup_cost_data[item][period],
    )
    model.holding_cost = pyo.Param(
        model.item_set,
        model.period_set,
        initialize=lambda mdl, item, period: holding_cost_data[item][period],
    )
    model.resource_capacity = pyo.Param(
        model.period_set,
        initialize=lambda mdl, period: capacity_data[period],
    )
    model.resource_usage = pyo.Param(
        model.item_set,
        initialize=lambda mdl, item: usage_data[item],
    )
    model.production_bound = pyo.Param(
        model.item_set,
        model.period_set,
        initialize=lambda mdl, item, period: production_bound_data[item][period],
    )

    model.production = pyo.Var(
        model.item_set, model.period_set, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.item_set, model.period_set, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.item_set, model.period_set, domain=pyo.Binary
    )

    def inventory_balance_rule(mdl, item, period):
        previous_inventory = (
            0 if period == 0 else mdl.inventory[item, period - 1]
        )
        return mdl.inventory[item, period] == (
            previous_inventory
            + mdl.production[item, period]
            - mdl.demand[item, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.item_set,
        model.period_set,
        rule=inventory_balance_rule,
    )

    def capacity_rule(mdl, period):
        return sum(
            mdl.resource_usage[item] * mdl.production[item, period]
            for item in mdl.item_set
        ) <= mdl.resource_capacity[period]

    model.capacity_limit = pyo.Constraint(
        model.period_set,
        rule=capacity_rule,
    )

    def setup_link_rule(mdl, item, period):
        return mdl.production[item, period] <= (
            mdl.production_bound[item, period] * mdl.setup[item, period]
        )

    model.setup_link = pyo.Constraint(
        model.item_set,
        model.period_set,
        rule=setup_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[item, period] * model.production[item, period]
            + model.setup_cost[item, period] * model.setup[item, period]
            + model.holding_cost[item, period] * model.inventory[item, period]
            for item in model.item_set
            for period in model.period_set
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}