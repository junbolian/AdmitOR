# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5,6,7]},"params":{"demand":"nonnegative[P,T]","production_cost":"nonnegative[P,T]","setup_cost":"nonnegative[P,T]","holding_cost":"nonnegative scalar, [P], or [P,T]","resource_usage":"nonnegative[P]","resource_capacity":"nonnegative[T]","production_limit":"nonnegative[P,T]"},"variables":{"production":"continuous nonnegative[P,T]","inventory":"continuous nonnegative[P,T]","setup":"binary[P,T]"},"constraints":["For each p,t: (0 if t=0 else inventory[p,t-1]) + production[p,t] - inventory[p,t] = demand[p,t].","For each t: sum_p resource_usage[p]*production[p,t] <= resource_capacity[t].","For each p,t: production[p,t] <= production_limit[p,t]*setup[p,t]."],"objective":"Minimize sum_{p,t}(production_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + holding_cost[p,t]*inventory[p,t]); broadcast scalar or product-specific holding costs across weeks."}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the three-product, eight-week production planning problem.

    Matrix inputs use zero-based nested indexing: data[product][week].
    resource_usage uses data[product]; resource_capacity uses data[week].
    holding_cost may be a scalar, a product vector, or a product-week matrix.
    Initial inventory is zero. No terminal inventory restriction is imposed.
    """
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    resource_usage = params["resource_usage"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    def holding_value(product, week):
        if isinstance(holding_cost, Number):
            return holding_cost
        product_cost = holding_cost[product]
        if isinstance(product_cost, Number):
            return product_cost
        return product_cost[week]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.weeks = pyo.RangeSet(0, 7)

    model.demand = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: demand[product][week],
        within=pyo.NonNegativeReals,
    )
    model.production_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: production_cost[product][week],
        within=pyo.NonNegativeReals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: setup_cost[product][week],
        within=pyo.NonNegativeReals,
    )
    model.holding_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: holding_value(product, week),
        within=pyo.NonNegativeReals,
    )
    model.resource_usage = pyo.Param(
        model.products,
        initialize=lambda mdl, product: resource_usage[product],
        within=pyo.NonNegativeReals,
    )
    model.resource_capacity = pyo.Param(
        model.weeks,
        initialize=lambda mdl, week: resource_capacity[week],
        within=pyo.NonNegativeReals,
    )
    model.production_limit = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: production_limit[product][week],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.weeks, domain=pyo.Binary
    )

    def inventory_balance_rule(mdl, product, week):
        starting_inventory = (
            0 if week == 0 else mdl.inventory[product, week - 1]
        )
        return (
            starting_inventory
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
                mdl.resource_usage[product] * mdl.production[product, week]
                for product in mdl.products
            )
            <= mdl.resource_capacity[week]
        )

    model.resource_capacity_constraint = pyo.Constraint(
        model.weeks, rule=resource_capacity_rule
    )

    def setup_link_rule(mdl, product, week):
        return (
            mdl.production[product, week]
            <= mdl.production_limit[product, week] * mdl.setup[product, week]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.weeks, rule=setup_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, week]
            * model.production[product, week]
            + model.setup_cost[product, week] * model.setup[product, week]
            + model.holding_cost[product, week] * model.inventory[product, week]
            for product in model.products
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when it cannot load a solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}