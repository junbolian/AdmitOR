# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3]},"params":{"profit_per_unit":"vector[product]","holding_cost":"scalar","grinder_capacity":"scalar","drill_capacity":"scalar","borer_capacity":"scalar","grinder_hours_per_unit":"vector[product]","drill_hours_per_unit":"vector[product]","borer_hours_per_unit":"vector[product]","inventory_limit":"scalar","sales_limit_product0":"vector[period]","sales_limit_product1":"vector[period]","target_inventory":"scalar"},"variables":{"production":"nonnegative continuous[product,period]","sales":"nonnegative continuous[product,period]","inventory":"nonnegative continuous[product,period]"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and t=1,2,3","sum_p grinder_hours_per_unit[p]*production[p,t] <= grinder_capacity for each period t","sum_p drill_hours_per_unit[p]*production[p,t] <= drill_capacity for each period t","sum_p borer_hours_per_unit[p]*production[p,t] <= borer_capacity for each period t","inventory[p,t] <= inventory_limit for each product p and period t","sales[0,t] <= sales_limit_product0[t] for each period t","sales[1,t] <= sales_limit_product1[t] for each period t","inventory[p,3] = target_inventory for each product p"],"objective":"maximize sum_p,t (profit_per_unit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.later_periods = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])

    model.grinder_capacity = pyo.Param(
        initialize=params["grinder_capacity"]
    )
    model.drill_capacity = pyo.Param(
        initialize=params["drill_capacity"]
    )
    model.borer_capacity = pyo.Param(
        initialize=params["borer_capacity"]
    )

    model.grinder_hours_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["grinder_hours_per_unit"][product]
            for product in model.products
        },
    )
    model.drill_hours_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["drill_hours_per_unit"][product]
            for product in model.products
        },
    )
    model.borer_hours_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["borer_hours_per_unit"][product]
            for product in model.products
        },
    )

    model.inventory_limit = pyo.Param(
        initialize=params["inventory_limit"]
    )
    model.sales_limit_product0 = pyo.Param(
        model.periods,
        initialize={
            period: params["sales_limit_product0"][period]
            for period in model.periods
        },
    )
    model.sales_limit_product1 = pyo.Param(
        model.periods,
        initialize={
            period: params["sales_limit_product1"][period]
            for period in model.periods
        },
    )
    model.target_inventory = pyo.Param(
        initialize=params["target_inventory"]
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

    def initial_balance_rule(instance, product):
        return (
            instance.production[product, 0]
            == instance.sales[product, 0] + instance.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(instance, product, period):
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=inventory_balance_rule,
    )

    def grinder_capacity_rule(instance, period):
        return (
            sum(
                instance.grinder_hours_per_unit[product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.grinder_capacity
        )

    model.grinder_capacity_constraints = pyo.Constraint(
        model.periods, rule=grinder_capacity_rule
    )

    def drill_capacity_rule(instance, period):
        return (
            sum(
                instance.drill_hours_per_unit[product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.drill_capacity
        )

    model.drill_capacity_constraints = pyo.Constraint(
        model.periods, rule=drill_capacity_rule
    )

    def borer_capacity_rule(instance, period):
        return (
            sum(
                instance.borer_hours_per_unit[product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.borer_capacity
        )

    model.borer_capacity_constraints = pyo.Constraint(
        model.periods, rule=borer_capacity_rule
    )

    def inventory_limit_rule(instance, product, period):
        return (
            instance.inventory[product, period]
            <= instance.inventory_limit
        )

    model.inventory_limit_constraints = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def product0_sales_limit_rule(instance, period):
        return (
            instance.sales[0, period]
            <= instance.sales_limit_product0[period]
        )

    model.product0_sales_limits = pyo.Constraint(
        model.periods, rule=product0_sales_limit_rule
    )

    def product1_sales_limit_rule(instance, period):
        return (
            instance.sales[1, period]
            <= instance.sales_limit_product1[period]
        )

    model.product1_sales_limits = pyo.Constraint(
        model.periods, rule=product1_sales_limit_rule
    )

    def target_inventory_rule(instance, product):
        return (
            instance.inventory[product, 3]
            == instance.target_inventory
        )

    model.ending_inventory_constraints = pyo.Constraint(
        model.products, rule=target_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_unavailable"}
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}