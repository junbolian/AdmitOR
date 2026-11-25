# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5,6,7]},"params":{"demand":"[P][T]","production_cost":"[P][T]","setup_cost":"[P][T]","holding_cost":"scalar","resource_usage":"[P]","resource_capacity":"[T]","production_limit":"[P][T]"},"variables":{"production[P,T]":"NonNegativeReals","inventory[P,T]":"NonNegativeReals","setup[P,T]":"Binary"},"constraints":["production[p,0] - inventory[p,0] = demand[p][0] for p in P","inventory[p,t-1] + production[p,t] - inventory[p,t] = demand[p][t] for p in P, t > 0","sum(resource_usage[p]*production[p,t] for p in P) <= resource_capacity[t] for t in T","production[p,t] <= production_limit[p][t]*setup[p,t] for p in P, t in T"],"objective":"min sum(production_cost[p][t]*production[p,t] + setup_cost[p][t]*setup[p,t] + holding_cost*inventory[p,t] for p in P for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the production planning problem; holding_cost is a scalar."""
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    resource_usage = params["resource_usage"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.weeks = pyo.RangeSet(0, 7)

    model.production = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.weeks, domain=pyo.Binary
    )

    def inventory_balance_rule(model, product, week):
        starting_inventory = (
            0 if week == 0 else model.inventory[product, week - 1]
        )
        return (
            starting_inventory
            + model.production[product, week]
            - model.inventory[product, week]
            == demand[product][week]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.weeks, rule=inventory_balance_rule
    )

    def resource_capacity_rule(model, week):
        return (
            sum(
                resource_usage[product] * model.production[product, week]
                for product in model.products
            )
            <= resource_capacity[week]
        )

    model.resource_constraints = pyo.Constraint(
        model.weeks, rule=resource_capacity_rule
    )

    def setup_link_rule(model, product, week):
        return (
            model.production[product, week]
            <= production_limit[product][week] * model.setup[product, week]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.weeks, rule=setup_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            production_cost[product][week] * model.production[product, week]
            + setup_cost[product][week] * model.setup[product, week]
            + holding_cost * model.inventory[product, week]
            for product in model.products
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}