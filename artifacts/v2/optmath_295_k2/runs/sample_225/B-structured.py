# IR: {"sets":{"P":["A","B"],"T":[0,1,2,3,4,5]},"params":{"cumulative_demand_A":"C[A,t]","cumulative_demand_B":"C[B,t]","production_cost_A":"c[A,t]","production_cost_B":"c[B,t]","setup_cost_A":"s[A,t]","setup_cost_B":"s[B,t]","holding_cost_A":"h[A,t]","holding_cost_B":"h[B,t]","resource_usage_A":"u[A]","resource_usage_B":"u[B]","resource_capacity":"R[t]"},"derived":{"d[p,t]":"C[p,t]-(C[p,t-1] if t>0 else 0)","U[p,t]":"C[p,5]-(C[p,t-1] if t>0 else 0)"},"variables":{"x[p,t]":"nonnegative continuous production","I[p,t]":"nonnegative continuous ending inventory","y[p,t]":"binary setup"},"constraints":["I[p,t]=(I[p,t-1] if t>0 else 0)+x[p,t]-d[p,t] for all p,t","x[p,t]<=U[p,t]*y[p,t] for all p,t","sum(p in P,u[p]*x[p,t])<=R[t] for all t","I[p,5]=0 for all p"],"objective":"minimize sum(p in P,t in T,c[p,t]*x[p,t]+s[p,t]*y[p,t]+h[p,t]*I[p,t])"}

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
        model.products,
        initialize=resource_usage,
    )
    model.resource_capacity = pyo.Param(
        model.months,
        initialize={
            month: resource_capacity[month]
            for month in months
        },
    )

    def monthly_demand_rule(instance, product, month):
        previous_cumulative = (
            instance.cumulative_demand[product, month - 1]
            if month > 0
            else 0
        )
        return instance.cumulative_demand[product, month] - previous_cumulative

    model.monthly_demand = pyo.Param(
        model.products,
        model.months,
        initialize=monthly_demand_rule,
    )

    def remaining_demand_rule(instance, product, month):
        previous_cumulative = (
            instance.cumulative_demand[product, month - 1]
            if month > 0
            else 0
        )
        return instance.cumulative_demand[product, 5] - previous_cumulative

    model.remaining_demand = pyo.Param(
        model.products,
        model.months,
        initialize=remaining_demand_rule,
    )

    model.production = pyo.Var(
        model.products,
        model.months,
        domain=pyo.NonNegativeReals,
    )
    model.inventory = pyo.Var(
        model.products,
        model.months,
        domain=pyo.NonNegativeReals,
    )
    model.setup = pyo.Var(
        model.products,
        model.months,
        domain=pyo.Binary,
    )

    def inventory_balance_rule(instance, product, month):
        previous_inventory = (
            instance.inventory[product, month - 1]
            if month > 0
            else 0
        )
        return (
            instance.inventory[product, month]
            == previous_inventory
            + instance.production[product, month]
            - instance.monthly_demand[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.months,
        rule=inventory_balance_rule,
    )

    def setup_link_rule(instance, product, month):
        return (
            instance.production[product, month]
            <= instance.remaining_demand[product, month]
            * instance.setup[product, month]
        )

    model.setup_link = pyo.Constraint(
        model.products,
        model.months,
        rule=setup_link_rule,
    )

    def resource_limit_rule(instance, month):
        return (
            sum(
                instance.resource_usage[product]
                * instance.production[product, month]
                for product in instance.products
            )
            <= instance.resource_capacity[month]
        )

    model.resource_limit = pyo.Constraint(
        model.months,
        rule=resource_limit_rule,
    )

    def terminal_inventory_rule(instance, product):
        return instance.inventory[product, 5] == 0

    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=terminal_inventory_rule,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}