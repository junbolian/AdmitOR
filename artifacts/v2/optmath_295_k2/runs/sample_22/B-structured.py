# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4]},"params":{"profit_per_unit":"[product]","holding_cost_per_unit_per_period":"scalar","grinder_hours":"[period]","drill_hours":"[period]","borer_hours":"[period]","machine_time_grinder":"[product]","machine_time_drill":"[product]","machine_time_borer":"[product]","inventory_capacity":"scalar","sales_limit":"[product][period]","target_final_inventory":"scalar"},"variables":{"production[product,period]":"nonnegative continuous","sales[product,period]":"nonnegative continuous","inventory[product,period]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum_p(machine_time_grinder[p]*production[p,t]) <= grinder_hours[t] for each period t","sum_p(machine_time_drill[p]*production[p,t]) <= drill_hours[t] for each period t","sum_p(machine_time_borer[p]*production[p,t]) <= borer_hours[t] for each period t","inventory[p,t] <= inventory_capacity for each product p and period t","sales[p,t] <= sales_limit[p][t] for each product p and period t","inventory[p,4] = target_final_inventory for each product p"],"objective":"maximize sum_(p,t)(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)

    # Mutable Params preserve symbolic expressions even when all machine
    # coefficients are zero, preventing constraints from becoming booleans.
    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda block, product: params["profit_per_unit"][product],
        mutable=True,
    )
    model.holding_cost_per_unit_per_period = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"],
        mutable=True,
    )
    model.grinder_hours = pyo.Param(
        model.periods,
        initialize=lambda block, period: params["grinder_hours"][period],
        mutable=True,
    )
    model.drill_hours = pyo.Param(
        model.periods,
        initialize=lambda block, period: params["drill_hours"][period],
        mutable=True,
    )
    model.borer_hours = pyo.Param(
        model.periods,
        initialize=lambda block, period: params["borer_hours"][period],
        mutable=True,
    )
    model.machine_time_grinder = pyo.Param(
        model.products,
        initialize=lambda block, product: params["machine_time_grinder"][product],
        mutable=True,
    )
    model.machine_time_drill = pyo.Param(
        model.products,
        initialize=lambda block, product: params["machine_time_drill"][product],
        mutable=True,
    )
    model.machine_time_borer = pyo.Param(
        model.products,
        initialize=lambda block, product: params["machine_time_borer"][product],
        mutable=True,
    )
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_capacity"],
        mutable=True,
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda block, product, period: params["sales_limit"][product][period],
        mutable=True,
    )
    model.target_final_inventory = pyo.Param(
        initialize=params["target_final_inventory"],
        mutable=True,
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

    def inventory_balance_rule(block, product, period):
        if period == 0:
            return (
                block.production[product, period]
                == block.sales[product, period] + block.inventory[product, period]
            )
        return (
            block.inventory[product, period - 1]
            + block.production[product, period]
            == block.sales[product, period] + block.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.periods,
        rule=inventory_balance_rule,
    )

    model.grinder_capacity = pyo.Constraint(
        model.periods,
        rule=lambda block, period: (
            sum(
                block.machine_time_grinder[product]
                * block.production[product, period]
                for product in block.products
            )
            <= block.grinder_hours[period]
        ),
    )
    model.drill_capacity = pyo.Constraint(
        model.periods,
        rule=lambda block, period: (
            sum(
                block.machine_time_drill[product]
                * block.production[product, period]
                for product in block.products
            )
            <= block.drill_hours[period]
        ),
    )
    model.borer_capacity = pyo.Constraint(
        model.periods,
        rule=lambda block, period: (
            sum(
                block.machine_time_borer[product]
                * block.production[product, period]
                for product in block.products
            )
            <= block.borer_hours[period]
        ),
    )
    model.inventory_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.inventory[product, period] <= block.inventory_capacity
        ),
    )
    model.sales_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.sales[product, period] <= block.sales_limit[product, period]
        ),
    )
    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda block, product: (
            block.inventory[product, 4] == block.target_final_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit_per_period
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}