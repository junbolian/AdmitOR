# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4],"T_after_initial":[1,2,3,4]},"params":{"profit_per_unit":"P-indexed","holding_cost_per_unit_per_period":"scalar","grinder_hours_per_unit":"P-indexed","drill_hours_per_unit":"P-indexed","borer_hours_per_unit":"P-indexed","grinder_capacity_per_period":"T-indexed","drill_capacity_per_period":"T-indexed","borer_capacity_per_period":"T-indexed","max_inventory_per_product":"scalar, applies to each product","sales_limits_product0":"T-indexed","sales_limits_product1":"T-indexed","sales_limits_product2":"T-indexed","target_inventory_end_period4":"scalar, applies to each product"},"variables":{"production[P,T]":"NonNegativeReals","sales[P,T]":"NonNegativeReals","inventory[P,T]":"NonNegativeReals"},"constraints":["initial_balance[p]: production[p,0] = sales[p,0] + inventory[p,0]","inventory_balance[p,t>0]: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t]","grinder_capacity[t]: sum_p grinder_hours_per_unit[p]*production[p,t] <= grinder_capacity_per_period[t]","drill_capacity[t]: sum_p drill_hours_per_unit[p]*production[p,t] <= drill_capacity_per_period[t]","borer_capacity[t]: sum_p borer_hours_per_unit[p]*production[p,t] <= borer_capacity_per_period[t]","inventory_limit[p,t]: inventory[p,t] <= max_inventory_per_product","sales_limit[p,t]: sales[p,t] <= sales_limits_product{p}[t]","ending_inventory[p]: inventory[p,4] = target_inventory_end_period4"],"objective":"maximize sum_(p,t) profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)
    model.later_periods = pyo.RangeSet(1, 4)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"]
    )

    model.grinder_usage = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["grinder_hours_per_unit"][product],
    )
    model.drill_usage = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["drill_hours_per_unit"][product],
    )
    model.borer_usage = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["borer_hours_per_unit"][product],
    )

    model.grinder_hours = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["grinder_capacity_per_period"][period],
    )
    model.drill_hours = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["drill_capacity_per_period"][period],
    )
    model.borer_hours = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["borer_capacity_per_period"][period],
    )

    model.inventory_capacity = pyo.Param(
        initialize=params["max_inventory_per_product"]
    )
    sales_limits = (
        params["sales_limits_product0"],
        params["sales_limits_product1"],
        params["sales_limits_product2"],
    )
    model.sales_capacity = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: sales_limits[product][period],
    )
    model.ending_inventory_target = pyo.Param(
        initialize=params["target_inventory_end_period4"]
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    model.initial_balance = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product, 0]
            == mdl.sales[product, 0] + mdl.inventory[product, 0]
        ),
    )
    model.inventory_balance = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period - 1] + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        ),
    )

    model.grinder_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.grinder_usage[product] * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.grinder_hours[period]
        ),
    )
    model.drill_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.drill_usage[product] * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.drill_hours[period]
        ),
    )
    model.borer_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.borer_usage[product] * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.borer_hours[period]
        ),
    )

    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_capacity
        ),
    )
    model.sales_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_capacity[product, period]
        ),
    )
    model.ending_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 4] == mdl.ending_inventory_target
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}