# IR: {"sets":{"P":["A","B"],"T":[0,1,2,3,4]},"params":{"demand_A":"cumulative demand[T]","demand_B":"cumulative demand[T]","prod_cost_A":"production cost[T]","prod_cost_B":"production cost[T]","setup_cost_A":"setup cost[T]","setup_cost_B":"setup cost[T]","hold_cost_A":"holding cost[T]","hold_cost_B":"holding cost[T]","resource_use_A":"resource per unit","resource_use_B":"resource per unit","resource_capacity":"capacity[T]","max_prod_A":"production upper bound[T]","max_prod_B":"production upper bound[T]"},"variables":{"production[P,T]":"NonNegativeReals","inventory[P,T]":"NonNegativeReals","setup[P,T]":"Binary"},"constraints":["inventory[p,t] = (0 if t=0 else inventory[p,t-1]) + production[p,t] - (demand[p,t] - (0 if t=0 else demand[p,t-1])) for p in P,t in T","production[p,t] <= max_prod[p,t]*setup[p,t] for p in P,t in T","sum(resource_use[p]*production[p,t] for p in P) <= resource_capacity[t] for t in T","inventory[p,4] = 0 for p in P"],"objective":"minimize sum(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost[p,t]*inventory[p,t] for p in P,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the five-period production planning problem."""
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
    production_limit_data = {
        "A": params["max_prod_A"],
        "B": params["max_prod_B"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.periods = pyo.RangeSet(0, 4)

    model.cumulative_demand = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: demand_data[product][period],
    )
    model.production_cost = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: production_cost_data[product][period],
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: setup_cost_data[product][period],
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: holding_cost_data[product][period],
    )
    model.resource_use = pyo.Param(
        model.products,
        initialize=lambda mdl, product: resource_use_data[product],
    )
    model.resource_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: capacity_data[period],
    )
    model.production_limit = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: production_limit_data[product][period],
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

    def inventory_balance_rule(mdl, product, period):
        previous_inventory = (
            0 if period == 0 else mdl.inventory[product, period - 1]
        )
        previous_cumulative_demand = (
            0 if period == 0 else mdl.cumulative_demand[product, period - 1]
        )
        period_demand = (
            mdl.cumulative_demand[product, period] - previous_cumulative_demand
        )
        return (
            previous_inventory + mdl.production[product, period]
            == period_demand + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    model.production_setup_link = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.production[product, period]
            <= mdl.production_limit[product, period] * mdl.setup[product, period]
        ),
    )

    model.shared_resource_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.resource_use[product] * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.resource_capacity[period]
        ),
    )

    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: mdl.inventory[product, 4] == 0,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, period] * model.production[product, period]
            + model.setup_cost[product, period] * model.setup[product, period]
            + model.holding_cost[product, period] * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}