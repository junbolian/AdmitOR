# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3]},"params":["revenue_product_0","revenue_product_1","revenue_product_2","holding_cost","grinder_capacity_period_0","grinder_capacity_periods_1_3","drill_capacity_periods_0_1_3","drill_capacity_period_2","borer_capacity_all_periods","max_inventory_per_product_per_period","sales_limit_p0","sales_limit_p1","sales_limit_p2","sales_limit_p3","final_inventory_required"],"assumptions":["Grinder and drill processing times are unspecified; assume one hour per produced unit on each machine.","Sales-limit parameters are sequences indexed by product.","Quantities are continuous; borer processing takes two hours per unit."],"variables":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p production[p,t] <= grinder_capacity[t]","sum_p production[p,t] <= drill_capacity[t]","2*sum_p production[p,t] <= borer_capacity_all_periods","inventory[p,t] <= max_inventory_per_product_per_period","sales[p,t] <= sales_limit[t][p]","inventory[p,3] = final_inventory_required"],"objective":"maximize sum_(p,t) revenue[p]*sales[p,t] - holding_cost*inventory[p,t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenues = {
        0: params["revenue_product_0"],
        1: params["revenue_product_1"],
        2: params["revenue_product_2"],
    }
    holding_cost = params["holding_cost"]
    grinder_initial = params["grinder_capacity_period_0"]
    grinder_later = params["grinder_capacity_periods_1_3"]
    drill_available = params["drill_capacity_periods_0_1_3"]
    drill_period_two = params["drill_capacity_period_2"]
    borer_capacity = params["borer_capacity_all_periods"]
    inventory_capacity = params["max_inventory_per_product_per_period"]
    sales_limits = {
        0: params["sales_limit_p0"],
        1: params["sales_limit_p1"],
        2: params["sales_limit_p2"],
        3: params["sales_limit_p3"],
    }
    final_inventory = params["final_inventory_required"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
        bounds=(0, inventory_capacity),
    )
    model.sales = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
        bounds=lambda mdl, product, period: (
            0, sales_limits[period][product]
        ),
    )

    def balance_rule(mdl, product, period):
        previous_inventory = (
            0 if period == 0 else mdl.inventory[product, period - 1]
        )
        return (
            previous_inventory + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def grinder_rule(mdl, period):
        capacity = grinder_initial if period == 0 else grinder_later
        return (
            sum(mdl.production[product, period] for product in mdl.products)
            <= capacity
        )

    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods, rule=grinder_rule
    )

    def drill_rule(mdl, period):
        capacity = drill_period_two if period == 2 else drill_available
        return (
            sum(mdl.production[product, period] for product in mdl.products)
            <= capacity
        )

    model.drill_capacity_constraint = pyo.Constraint(
        model.periods, rule=drill_rule
    )
    model.borer_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            2 * sum(
                mdl.production[product, period] for product in mdl.products
            )
            <= borer_capacity
        ),
    )
    model.final_inventory_constraint = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == final_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            revenues[product] * model.sales[product, period]
            - holding_cost * model.inventory[product, period]
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