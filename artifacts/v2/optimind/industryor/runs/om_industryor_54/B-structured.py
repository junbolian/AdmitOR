# IR: {"sets":{"T":[1,2,3],"T0":[0,1,2,3]},"params":{"warehouse_capacity":"nonnegative scalar","initial_inventory":"nonnegative scalar","initial_funds":"nonnegative scalar","purchase_price":"length-3 sequence, Jan-Mar","selling_price":"length-3 sequence, Jan-Mar","terminal_inventory_requirement":"nonnegative scalar"},"variables":{"buy[t in T]":"nonnegative continuous","sell[t in T]":"nonnegative continuous","inventory[t in T0]":"continuous, 0 <= inventory <= warehouse_capacity","cash[t in T0]":"nonnegative continuous"},"assumptions":["Each month, sales of beginning inventory may precede purchases; current-month sales receipts may finance purchases.","Terminal inventory equals the required quantity.","Profit is total sales receipts minus total purchase payments; no terminal inventory valuation is specified."],"constraints":["inventory[0] = initial_inventory","cash[0] = initial_funds","sell[t] <= inventory[t-1] for t in T","inventory[t] = inventory[t-1] + buy[t] - sell[t] for t in T","cash[t] = cash[t-1] + selling_price[t]*sell[t] - purchase_price[t]*buy[t] for t in T","inventory[3] = terminal_inventory_requirement"],"objective":"maximize sum(selling_price[t]*sell[t] - purchase_price[t]*buy[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the quarterly grain-trading LP; prices are Jan-Mar sequences."""
    model = pyo.ConcreteModel()

    model.months = pyo.RangeSet(1, 3)
    model.periods = pyo.RangeSet(0, 3)

    model.warehouse_capacity = pyo.Param(
        initialize=params["warehouse_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.initial_inventory = pyo.Param(
        initialize=params["initial_inventory"],
        within=pyo.NonNegativeReals,
    )
    model.initial_funds = pyo.Param(
        initialize=params["initial_funds"],
        within=pyo.NonNegativeReals,
    )
    model.purchase_price = pyo.Param(
        model.months,
        initialize={
            t: params["purchase_price"][t - 1] for t in model.months
        },
        within=pyo.Reals,
    )
    model.selling_price = pyo.Param(
        model.months,
        initialize={
            t: params["selling_price"][t - 1] for t in model.months
        },
        within=pyo.Reals,
    )
    model.terminal_inventory_requirement = pyo.Param(
        initialize=params["terminal_inventory_requirement"],
        within=pyo.NonNegativeReals,
    )

    model.buy = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(
        model.periods,
        domain=pyo.NonNegativeReals,
        bounds=(0, model.warehouse_capacity),
    )
    model.cash = pyo.Var(model.periods, domain=pyo.NonNegativeReals)

    model.starting_inventory_constraint = pyo.Constraint(
        expr=model.inventory[0] == model.initial_inventory
    )
    model.starting_cash_constraint = pyo.Constraint(
        expr=model.cash[0] == model.initial_funds
    )

    def sale_availability_rule(current_model, t):
        return current_model.sell[t] <= current_model.inventory[t - 1]

    model.sale_availability = pyo.Constraint(
        model.months, rule=sale_availability_rule
    )

    def inventory_balance_rule(current_model, t):
        return (
            current_model.inventory[t]
            == current_model.inventory[t - 1]
            + current_model.buy[t]
            - current_model.sell[t]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    def cash_balance_rule(current_model, t):
        return (
            current_model.cash[t]
            == current_model.cash[t - 1]
            + current_model.selling_price[t] * current_model.sell[t]
            - current_model.purchase_price[t] * current_model.buy[t]
        )

    model.cash_balance = pyo.Constraint(
        model.months, rule=cash_balance_rule
    )
    model.terminal_inventory_constraint = pyo.Constraint(
        expr=model.inventory[3] == model.terminal_inventory_requirement
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.selling_price[t] * model.sell[t]
            - model.purchase_price[t] * model.buy[t]
            for t in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        # Still use objective retrieval as the sole success test.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}