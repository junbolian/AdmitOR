# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5]},"params":{"demand":"P x T, from params","production_cost":"P x T, from params","setup_cost":"P x T, from params","holding_cost":"P, from params","capacity":"T, from params","capacity_consumption":"P, from params"},"variables":{"production":"P x T, continuous nonnegative","inventory":"P x T, continuous nonnegative","setup":"P x T, binary"},"constraints":{"inventory_balance":"For each i,t: sum(production[i,k] for k<=t) = sum(demand[i,k] for k<=t) + inventory[i,t]; no separate initial-inventory variable or terminal-inventory constraint","monthly_capacity":"For each t: sum(capacity_consumption[i]*production[i,t] for i in P) <= capacity[t]","setup_link":"For each i,t: production[i,t] <= setup[i,t]*sum(demand[i,k] for k>=t)"},"objective":"Minimize sum(production_cost[i,t]*production[i,t] + setup_cost[i,t]*setup[i,t] + holding_cost[i]*inventory[i,t] for i in P,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.months = pyo.RangeSet(0, 5)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, i, t: demand[i][t],
        within=pyo.Reals,
    )
    model.production_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, i, t: production_cost[i][t],
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, i, t: setup_cost[i][t],
        within=pyo.Reals,
    )
    model.holding_cost = pyo.Param(
        model.products,
        initialize=lambda mdl, i: holding_cost[i],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.months,
        initialize=lambda mdl, t: capacity[t],
        within=pyo.Reals,
    )
    model.capacity_consumption = pyo.Param(
        model.products,
        initialize=lambda mdl, i: capacity_consumption[i],
        within=pyo.Reals,
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

    def inventory_balance_rule(mdl, i, t):
        return (
            sum(mdl.production[i, k] for k in mdl.months if k <= t)
            == sum(mdl.demand[i, k] for k in mdl.months if k <= t)
            + mdl.inventory[i, t]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def monthly_capacity_rule(mdl, t):
        return (
            sum(
                mdl.capacity_consumption[i] * mdl.production[i, t]
                for i in mdl.products
            )
            <= mdl.capacity[t]
        )

    model.monthly_capacity = pyo.Constraint(
        model.months, rule=monthly_capacity_rule
    )

    def setup_link_rule(mdl, i, t):
        return mdl.production[i, t] <= mdl.setup[i, t] * sum(
            mdl.demand[i, k] for k in mdl.months if k >= t
        )

    model.setup_link = pyo.Constraint(
        model.products, model.months, rule=setup_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[i, t] * model.production[i, t]
            + model.setup_cost[i, t] * model.setup[i, t]
            + model.holding_cost[i] * model.inventory[i, t]
            for i in model.products
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Success depends solely on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}