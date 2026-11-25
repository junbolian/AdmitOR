# IR: {"sets":{"products":["A","B"],"months":[0,1,2,3,4,5]},"params":{"cumulative_demand_A":"params['cumulative_demand_A']","cumulative_demand_B":"params['cumulative_demand_B']","production_cost_A":"params['production_cost_A']","production_cost_B":"params['production_cost_B']","setup_cost_A":"params['setup_cost_A']","setup_cost_B":"params['setup_cost_B']","holding_cost_A":"params['holding_cost_A']","holding_cost_B":"params['holding_cost_B']","resource_usage_A":"params['resource_usage_A']","resource_usage_B":"params['resource_usage_B']","resource_capacity":"params['resource_capacity']"},"derived":{"D[p,t]":"cumulative_demand_p[t]","d[p,t]":"D[p,t]-(D[p,t-1] if t>0 else 0)","remaining[p,t]":"D[p,5]-(D[p,t-1] if t>0 else 0)"},"variables":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","setup[p,t]":"binary"},"constraints":["inventory[p,t]=(inventory[p,t-1] if t>0 else 0)+production[p,t]-d[p,t] for all p,t","production[p,t]<=remaining[p,t]*setup[p,t] for all p,t","sum(resource_usage_p*production[p,t] for p)<=resource_capacity[t] for all t","inventory[p,5]=0 for all p"],"objective":"minimize sum(production_cost_p[t]*production[p,t]+setup_cost_p[t]*setup[p,t]+holding_cost_p[t]*inventory[p,t] for p,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("A", "B")
    months = tuple(range(6))

    cumulative_demand = {
        "A": params["cumulative_demand_A"],
        "B": params["cumulative_demand_B"],
    }
    production_cost = {
        "A": params["production_cost_A"],
        "B": params["production_cost_B"],
    }
    setup_cost = {
        "A": params["setup_cost_A"],
        "B": params["setup_cost_B"],
    }
    holding_cost = {
        "A": params["holding_cost_A"],
        "B": params["holding_cost_B"],
    }
    resource_usage = {
        "A": params["resource_usage_A"],
        "B": params["resource_usage_B"],
    }
    resource_capacity = params["resource_capacity"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.months = pyo.Set(initialize=months, ordered=True)

    model.cumulative_demand = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): cumulative_demand[product][month]
            for product in products
            for month in months
        },
    )
    model.production_cost = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): production_cost[product][month]
            for product in products
            for month in months
        },
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): setup_cost[product][month]
            for product in products
            for month in months
        },
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): holding_cost[product][month]
            for product in products
            for month in months
        },
    )
    model.resource_usage = pyo.Param(
        model.products, initialize=resource_usage
    )
    model.resource_capacity = pyo.Param(
        model.months,
        initialize={month: resource_capacity[month] for month in months},
    )

    def demand_rule(block, product, month):
        previous_demand = (
            block.cumulative_demand[product, month - 1]
            if month > 0
            else 0
        )
        return block.cumulative_demand[product, month] - previous_demand

    model.monthly_demand = pyo.Expression(
        model.products, model.months, rule=demand_rule
    )

    def remaining_demand_rule(block, product, month):
        previous_demand = (
            block.cumulative_demand[product, month - 1]
            if month > 0
            else 0
        )
        return block.cumulative_demand[product, 5] - previous_demand

    model.remaining_demand = pyo.Expression(
        model.products, model.months, rule=remaining_demand_rule
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

    def inventory_balance_rule(block, product, month):
        previous_inventory = (
            block.inventory[product, month - 1] if month > 0 else 0
        )
        return (
            block.inventory[product, month]
            == previous_inventory
            + block.production[product, month]
            - block.monthly_demand[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def production_setup_rule(block, product, month):
        return (
            block.production[product, month]
            <= block.remaining_demand[product, month]
            * block.setup[product, month]
        )

    model.production_setup_limit = pyo.Constraint(
        model.products, model.months, rule=production_setup_rule
    )

    def resource_capacity_rule(block, month):
        return (
            sum(
                block.resource_usage[product]
                * block.production[product, month]
                for product in block.products
            )
            <= block.resource_capacity[month]
        )

    model.shared_resource_limit = pyo.Constraint(
        model.months, rule=resource_capacity_rule
    )

    def terminal_inventory_rule(block, product):
        return block.inventory[product, 5] == 0

    model.terminal_inventory = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}