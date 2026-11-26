# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"warehouse_capacity":"scalar","initial_inventory":"scalar","purchase_prices":"length-6 vector indexed by T","sale_prices":"length-6 vector indexed by T"},"variables":{"purchase[t]":"nonnegative real","sales[t]":"nonnegative real","inventory[t]":"nonnegative real, end-of-month"},"constraints":["inventory[0] = initial_inventory + purchase[0] - sales[0]","inventory[t] = inventory[t-1] + purchase[t] - sales[t], t=1..5","initial_inventory + purchase[0] <= warehouse_capacity","inventory[t-1] + purchase[t] <= warehouse_capacity, t=1..5"],"objective":"maximize sum(sale_prices[t]*sales[t] - purchase_prices[t]*purchase[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_prices = params["purchase_prices"]
    sale_prices = params["sale_prices"]

    if len(purchase_prices) != 6 or len(sale_prices) != 6:
        raise ValueError("Each price vector must contain six monthly prices.")

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(0, 5)

    model.warehouse_capacity = pyo.Param(initialize=warehouse_capacity)
    model.initial_inventory = pyo.Param(initialize=initial_inventory)
    model.purchase_prices = pyo.Param(
        model.months,
        initialize={t: purchase_prices[t] for t in range(6)},
    )
    model.sale_prices = pyo.Param(
        model.months,
        initialize={t: sale_prices[t] for t in range(6)},
    )

    model.purchase = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(instance, t):
        starting_inventory = (
            instance.initial_inventory if t == 0 else instance.inventory[t - 1]
        )
        return (
            instance.inventory[t]
            == starting_inventory + instance.purchase[t] - instance.sales[t]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    def warehouse_limit_rule(instance, t):
        starting_inventory = (
            instance.initial_inventory if t == 0 else instance.inventory[t - 1]
        )
        return (
            starting_inventory + instance.purchase[t]
            <= instance.warehouse_capacity
        )

    model.warehouse_limit = pyo.Constraint(
        model.months, rule=warehouse_limit_rule
    )

    model.total_net_revenue = pyo.Objective(
        expr=sum(
            model.sale_prices[t] * model.sales[t]
            - model.purchase_prices[t] * model.purchase[t]
            for t in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when it cannot load a feasible solution.
        # Still use objective retrieval as the sole success criterion.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_net_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}