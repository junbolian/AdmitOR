# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5,6,7]},"params":{"demand":"nonnegative[P,T]","prod_cost":"real[P,T]","setup_cost":"real[P,T]","hold_cost":"real scalar","res_usage":"nonnegative[P]","res_capacity":"nonnegative[T]","prod_max":"nonnegative[P,T]","initial_inventory":"nonnegative[P]"},"variables":{"production":"continuous nonnegative[P,T]","inventory":"continuous nonnegative[P,T]","setup":"binary[P,T]"},"constraints":["For each p: initial_inventory[p] + production[p,0] - inventory[p,0] = demand[p,0].","For each p,t>0: inventory[p,t-1] + production[p,t] - inventory[p,t] = demand[p,t].","For each t: sum_p res_usage[p]*production[p,t] <= res_capacity[t].","For each p,t: production[p,t] <= prod_max[p,t]*setup[p,t]."],"objective":"Minimize sum_{p,t}(prod_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + hold_cost*inventory[p,t])."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the three-product, eight-week production planning problem.

    Input layout:
        demand, prod_cost, setup_cost, prod_max: nested arrays [product][week]
        res_usage, initial_inventory: arrays [product]
        res_capacity: array [week]
        hold_cost: scalar

    Production and inventory quantities are continuous.
    """
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.weeks = pyo.RangeSet(0, 7)

    model.demand = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: params["demand"][product][week],
        within=pyo.NonNegativeReals,
    )
    model.prod_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: params["prod_cost"][product][week],
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: params["setup_cost"][product][week],
        within=pyo.Reals,
    )
    model.hold_cost = pyo.Param(
        initialize=params["hold_cost"],
        within=pyo.Reals,
    )
    model.res_usage = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["res_usage"][product],
        within=pyo.NonNegativeReals,
    )
    model.res_capacity = pyo.Param(
        model.weeks,
        initialize=lambda mdl, week: params["res_capacity"][week],
        within=pyo.NonNegativeReals,
    )
    model.prod_max = pyo.Param(
        model.products,
        model.weeks,
        initialize=lambda mdl, product, week: params["prod_max"][product][week],
        within=pyo.NonNegativeReals,
    )
    model.initial_inventory = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["initial_inventory"][product],
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
            mdl.initial_inventory[product]
            if week == 0
            else mdl.inventory[product, week - 1]
        )
        return (
            starting_inventory
            + mdl.production[product, week]
            - mdl.inventory[product, week]
            == mdl.demand[product, week]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.weeks,
        rule=inventory_balance_rule,
    )

    def resource_capacity_rule(mdl, week):
        return (
            sum(
                mdl.res_usage[product] * mdl.production[product, week]
                for product in mdl.products
            )
            <= mdl.res_capacity[week]
        )

    model.resource_capacity = pyo.Constraint(
        model.weeks,
        rule=resource_capacity_rule,
    )

    def production_setup_rule(mdl, product, week):
        return (
            mdl.production[product, week]
            <= mdl.prod_max[product, week] * mdl.setup[product, week]
        )

    model.production_setup = pyo.Constraint(
        model.products,
        model.weeks,
        rule=production_setup_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.prod_cost[product, week] * model.production[product, week]
            + model.setup_cost[product, week] * model.setup[product, week]
            + model.hold_cost * model.inventory[product, week]
            for product in model.products
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}