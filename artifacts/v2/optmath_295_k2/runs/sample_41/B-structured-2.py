# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3],"R":["grinder","drill","borer"]},"params":{"profit_product0":"scalar","profit_product1":"scalar","profit_product2":"scalar","holding_cost":"scalar","grinder_capacity":"scalar","drill_capacity":"scalar","borer_capacity":"scalar","grinder_hours_per_unit":"vector[P]","drill_hours_per_unit":"vector[P]","borer_hours_per_unit":"vector[P]","inventory_capacity":"scalar","sales_limit_product0":"vector[T]","sales_limit_product1":"vector[T]","sales_limit_product2":"vector[T]","final_inventory_target":"scalar"},"variables":{"production[P,T]":"continuous nonnegative","sales[P,T]":"continuous nonnegative","inventory[P,T]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in T with t>0","sum(hours[r,p]*production[p,t] for p in P) <= capacity[r] for r in R, t in T","inventory[p,t] <= inventory_capacity for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = final_inventory_target for p in P"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)
    model.resources = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    profit_data = {
        0: params["profit_product0"],
        1: params["profit_product1"],
        2: params["profit_product2"],
    }
    capacity_data = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }
    hours_data = {
        "grinder": params["grinder_hours_per_unit"],
        "drill": params["drill_hours_per_unit"],
        "borer": params["borer_hours_per_unit"],
    }
    sales_limit_data = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
        2: params["sales_limit_product2"],
    }

    model.unit_profit = pyo.Param(
        model.products, initialize=profit_data
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])
    model.machine_capacity = pyo.Param(
        model.resources, initialize=capacity_data
    )
    model.machine_hours = pyo.Param(
        model.resources,
        model.products,
        initialize={
            (resource, product): hours_data[resource][product]
            for resource in model.resources
            for product in model.products
        },
    )
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_capacity"]
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limit_data[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.final_inventory_target = pyo.Param(
        initialize=params["final_inventory_target"]
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

    def inventory_balance_rule(instance, product, period):
        if period == 0:
            return (
                instance.production[product, period]
                == instance.sales[product, period]
                + instance.inventory[product, period]
            )
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(instance, resource, period):
        return (
            sum(
                instance.machine_hours[resource, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.machine_capacity[resource]
        )

    model.machine_capacity_limit = pyo.Constraint(
        model.resources, model.periods, rule=machine_capacity_rule
    )

    model.inventory_storage_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period]
            <= instance.inventory_capacity
        ),
    )
    model.sales_demand_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period]
            <= instance.sales_limit[product, period]
        ),
    )
    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 3]
            == instance.final_inventory_target
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
    except RuntimeError as exc:
        if not str(exc).startswith(
            "A feasible solution was not found, so no solution can be loaded."
        ):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}