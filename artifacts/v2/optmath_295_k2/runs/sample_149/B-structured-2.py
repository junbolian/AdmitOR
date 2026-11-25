# IR: {"sets":{"P":["A","B"],"T":[0,1,2,3,4]},"params":{"demand_A":"cumulative demand[T]","demand_B":"cumulative demand[T]","prod_cost_A":"production cost[T]","prod_cost_B":"production cost[T]","setup_cost_A":"setup cost[T]","setup_cost_B":"setup cost[T]","hold_cost_A":"holding cost[T]","hold_cost_B":"holding cost[T]","resource_use_A":"resource use per unit","resource_use_B":"resource use per unit","resource_capacity":"capacity[T]","max_prod_A":"production upper bound[T]","max_prod_B":"production upper bound[T]"},"variables":{"production[P,T]":"continuous nonnegative","inventory[P,T]":"continuous nonnegative","setup[P,T]":"binary"},"constraints":["balance[p,t]: inventory[p,t] = (inventory[p,t-1] if t>0 else 0) + production[p,t] - (demand[p,t] - (demand[p,t-1] if t>0 else 0))","setup_link[p,t]: production[p,t] <= max_prod[p,t]*setup[p,t]","resource_limit[t]: sum(resource_use[p]*production[p,t] for p in P) <= resource_capacity[t]","terminal_inventory[p]: inventory[p,4] = 0"],"objective":"minimize sum(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost[p,t]*inventory[p,t] for p in P for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("A", "B")
    periods = range(5)

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
    resource_use_data = {
        "A": params["resource_use_A"],
        "B": params["resource_use_B"],
    }
    capacity_data = params["resource_capacity"]
    maximum_production_data = {
        "A": params["max_prod_A"],
        "B": params["max_prod_B"],
    }

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products, ordered=True)
    model.T = pyo.Set(initialize=periods, ordered=True)

    model.demand = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): demand_data[product][period]
            for product in products
            for period in periods
        },
    )
    model.prod_cost = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): production_cost_data[product][period]
            for product in products
            for period in periods
        },
    )
    model.setup_cost = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): setup_cost_data[product][period]
            for product in products
            for period in periods
        },
    )
    model.hold_cost = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): holding_cost_data[product][period]
            for product in products
            for period in periods
        },
    )
    model.resource_use = pyo.Param(
        model.P, initialize=resource_use_data
    )
    model.resource_capacity = pyo.Param(
        model.T,
        initialize={period: capacity_data[period] for period in periods},
    )
    model.max_prod = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): maximum_production_data[product][period]
            for product in products
            for period in periods
        },
    )

    model.production = pyo.Var(
        model.P, model.T, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.P, model.T, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(model.P, model.T, domain=pyo.Binary)

    def balance_rule(problem, product, period):
        previous_inventory = (
            problem.inventory[product, period - 1] if period > 0 else 0
        )
        previous_cumulative_demand = (
            problem.demand[product, period - 1] if period > 0 else 0
        )
        period_demand = (
            problem.demand[product, period] - previous_cumulative_demand
        )
        return problem.inventory[product, period] == (
            previous_inventory
            + problem.production[product, period]
            - period_demand
        )

    model.balance = pyo.Constraint(
        model.P, model.T, rule=balance_rule
    )

    def setup_link_rule(problem, product, period):
        return problem.production[product, period] <= (
            problem.max_prod[product, period]
            * problem.setup[product, period]
        )

    model.setup_link = pyo.Constraint(
        model.P, model.T, rule=setup_link_rule
    )

    def resource_limit_rule(problem, period):
        return sum(
            problem.resource_use[product]
            * problem.production[product, period]
            for product in problem.P
        ) <= problem.resource_capacity[period]

    model.resource_limit = pyo.Constraint(
        model.T, rule=resource_limit_rule
    )

    def terminal_inventory_rule(problem, product):
        return problem.inventory[product, 4] == 0

    model.terminal_inventory = pyo.Constraint(
        model.P, rule=terminal_inventory_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.prod_cost[product, period]
            * model.production[product, period]
            + model.setup_cost[product, period]
            * model.setup[product, period]
            + model.hold_cost[product, period]
            * model.inventory[product, period]
            for product in model.P
            for period in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Preserve unexpected solver exceptions.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}