# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3],"R":["grinder","drill","borer"]},"params":{"profit_per_unit":"P-vector","holding_cost_per_unit_month":"scalar","machine_hours_grinder":"T-vector","machine_hours_drill":"T-vector","machine_hours_borer":"T-vector","machine_time_grinder":"P-vector","machine_time_drill":"P-vector","machine_time_borer":"P-vector","max_inventory":"scalar","sales_limit":"P-by-T matrix","target_final_inventory":"P-vector"},"variables":{"production[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in T with t>0","sum(machine_time[r,p]*production[p,t] for p in P) <= machine_hours[r,t] for r in R, t in T","inventory[p,t] <= max_inventory for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = target_final_inventory[p] for p in P"],"objective":"maximize sum(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_month*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based product/month vectors and a product-by-month matrix."""
    products = range(3)
    months = range(4)
    machines = ("grinder", "drill", "borer")

    profit_data = params["profit_per_unit"]
    holding_cost_data = params["holding_cost_per_unit_month"]
    inventory_limit_data = params["max_inventory"]
    sales_limit_data = params["sales_limit"]
    final_inventory_data = params["target_final_inventory"]

    machine_hours_data = {
        "grinder": params["machine_hours_grinder"],
        "drill": params["machine_hours_drill"],
        "borer": params["machine_hours_borer"],
    }
    machine_time_data = {
        "grinder": params["machine_time_grinder"],
        "drill": params["machine_time_drill"],
        "borer": params["machine_time_borer"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.months = pyo.Set(initialize=months, ordered=True)
    model.machines = pyo.Set(initialize=machines, ordered=True)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={p: profit_data[p] for p in products},
    )
    model.holding_cost_per_unit_month = pyo.Param(
        initialize=holding_cost_data,
    )
    model.max_inventory = pyo.Param(
        initialize=inventory_limit_data,
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.months,
        initialize={
            (p, t): sales_limit_data[p][t]
            for p in products
            for t in months
        },
    )
    model.target_final_inventory = pyo.Param(
        model.products,
        initialize={p: final_inventory_data[p] for p in products},
    )
    model.machine_hours = pyo.Param(
        model.machines,
        model.months,
        initialize={
            (r, t): machine_hours_data[r][t]
            for r in machines
            for t in months
        },
    )
    model.machine_time = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (r, p): machine_time_data[r][p]
            for r in machines
            for p in products
        },
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(factory, p, t):
        if t == 0:
            return (
                factory.production[p, t]
                == factory.sales[p, t] + factory.inventory[p, t]
            )
        return (
            factory.inventory[p, t - 1] + factory.production[p, t]
            == factory.sales[p, t] + factory.inventory[p, t]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.months,
        rule=inventory_balance_rule,
    )

    def machine_capacity_rule(factory, r, t):
        return (
            sum(
                factory.machine_time[r, p] * factory.production[p, t]
                for p in factory.products
            )
            <= factory.machine_hours[r, t]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines,
        model.months,
        rule=machine_capacity_rule,
    )

    model.inventory_capacity = pyo.Constraint(
        model.products,
        model.months,
        rule=lambda factory, p, t: (
            factory.inventory[p, t] <= factory.max_inventory
        ),
    )
    model.sales_capacity = pyo.Constraint(
        model.products,
        model.months,
        rule=lambda factory, p, t: (
            factory.sales[p, t] <= factory.sales_limit[p, t]
        ),
    )
    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda factory, p: (
            factory.inventory[p, 3] == factory.target_final_inventory[p]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[p] * model.sales[p, t]
            - model.holding_cost_per_unit_month * model.inventory[p, t]
            for p in model.products
            for t in model.months
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