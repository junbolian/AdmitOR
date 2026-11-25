# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":["profit_product0","profit_product1","holding_cost","grinder_capacity","drill_capacity","borer_capacity","time_product0_grinder","time_product0_drill","time_product0_borer","time_product1_grinder","time_product1_drill","time_product1_borer","inventory_limit","sales_limit_product0","sales_limit_product1","target_inventory"],"variables":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t=1,2,3","sum_p time[p,k]*production[p,t] <= capacity[k] for each machine k and period t","inventory[p,t] <= inventory_limit","sales[p,t] <= sales_limit_productp[t]","inventory[p,3] = target_inventory"],"objective":"maximize sum_{p,t}(profit[p]*sales[p,t] - holding_cost*inventory[p,t])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Sales-limit parameters must be sequences or mappings indexed by period."""
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    model.profit = pyo.Param(
        model.products,
        initialize={
            0: params["profit_product0"],
            1: params["profit_product1"],
        },
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])
    model.capacity = pyo.Param(
        model.machines,
        initialize={
            "grinder": params["grinder_capacity"],
            "drill": params["drill_capacity"],
            "borer": params["borer_capacity"],
        },
    )
    model.processing_time = pyo.Param(
        model.products,
        model.machines,
        initialize={
            (0, "grinder"): params["time_product0_grinder"],
            (0, "drill"): params["time_product0_drill"],
            (0, "borer"): params["time_product0_borer"],
            (1, "grinder"): params["time_product1_grinder"],
            (1, "drill"): params["time_product1_drill"],
            (1, "borer"): params["time_product1_borer"],
        },
    )
    model.inventory_limit = pyo.Param(initialize=params["inventory_limit"])
    model.target_inventory = pyo.Param(initialize=params["target_inventory"])

    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.products
            for period in model.periods
        },
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def balance_rule(model, product, period):
        if period == 0:
            return (
                model.production[product, period]
                == model.sales[product, period] + model.inventory[product, period]
            )
        return (
            model.inventory[product, period - 1]
            + model.production[product, period]
            == model.sales[product, period] + model.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def capacity_rule(model, machine, period):
        return (
            sum(
                model.processing_time[product, machine]
                * model.production[product, period]
                for product in model.products
            )
            <= model.capacity[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )
    model.storage_bound = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda model, product, period: (
            model.inventory[product, period] <= model.inventory_limit
        ),
    )
    model.sales_bound = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda model, product, period: (
            model.sales[product, period] <= model.sales_limit[product, period]
        ),
    )
    model.final_inventory = pyo.Constraint(
        model.products,
        rule=lambda model, product: (
            model.inventory[product, 3] == model.target_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}