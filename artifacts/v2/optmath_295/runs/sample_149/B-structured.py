# IR: {"sets":{"P":["A","B"],"T":[0,1,2,3,4]},"params":{"demand_A_cumulative":"array[T]","demand_B_cumulative":"array[T]","prod_cost_A":"array[T]","prod_cost_B":"array[T]","setup_cost_A":"array[T]","setup_cost_B":"array[T]","hold_cost_A":"array[T]","hold_cost_B":"array[T]","resource_use_A":"scalar","resource_use_B":"scalar","resource_capacity":"array[T]","max_prod_A":"array[T]","max_prod_B":"array[T]"},"variables":{"production[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous","setup[P,T]":"binary"},"constraints":["For each product p and period t: sum(production[p,k] for k<=t) = demand_p_cumulative[t] + inventory[p,t] (zero initial inventory).","For each product p and period t: production[p,t] <= max_prod_p[t]*setup[p,t].","For each period t: resource_use_A*production[A,t] + resource_use_B*production[B,t] <= resource_capacity[t].","For each product p: inventory[p,4] = 0."],"objective":"Minimize sum(prod_cost_p[t]*production[p,t] + setup_cost_p[t]*setup[p,t] + hold_cost_p[t]*inventory[p,t] for p in P, t in T)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = {
        "A": params["demand_A_cumulative"],
        "B": params["demand_B_cumulative"],
    }
    production_cost = {
        "A": params["prod_cost_A"],
        "B": params["prod_cost_B"],
    }
    setup_cost = {
        "A": params["setup_cost_A"],
        "B": params["setup_cost_B"],
    }
    holding_cost = {
        "A": params["hold_cost_A"],
        "B": params["hold_cost_B"],
    }
    resource_use = {
        "A": params["resource_use_A"],
        "B": params["resource_use_B"],
    }
    capacity = params["resource_capacity"]
    production_limit = {
        "A": params["max_prod_A"],
        "B": params["max_prod_B"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.periods = pyo.RangeSet(0, 4)

    model.cumulative_demand = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: demand[product][period],
    )
    model.production_unit_cost = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: production_cost[product][period],
    )
    model.setup_unit_cost = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: setup_cost[product][period],
    )
    model.holding_unit_cost = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: holding_cost[product][period],
    )
    model.resource_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: resource_use[product],
    )
    model.available_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: capacity[period],
    )
    model.production_upper_bound = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: production_limit[product][period],
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

    def cumulative_balance_rule(mdl, product, period):
        return (
            sum(
                mdl.production[product, earlier_period]
                for earlier_period in mdl.periods
                if earlier_period <= period
            )
            == mdl.cumulative_demand[product, period]
            + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.periods,
        rule=cumulative_balance_rule,
    )

    def setup_link_rule(mdl, product, period):
        return (
            mdl.production[product, period]
            <= mdl.production_upper_bound[product, period]
            * mdl.setup[product, period]
        )

    model.setup_link = pyo.Constraint(
        model.products,
        model.periods,
        rule=setup_link_rule,
    )

    def resource_capacity_rule(mdl, period):
        return (
            sum(
                mdl.resource_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.available_capacity[period]
        )

    model.resource_constraint = pyo.Constraint(
        model.periods,
        rule=resource_capacity_rule,
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: mdl.inventory[product, 4] == 0,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_unit_cost[product, period]
            * model.production[product, period]
            + model.setup_unit_cost[product, period]
            * model.setup[product, period]
            + model.holding_unit_cost[product, period]
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}