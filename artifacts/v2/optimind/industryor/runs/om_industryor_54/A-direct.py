import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    initial_funds = params["initial_funds"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]
    terminal_inventory_requirement = params["terminal_inventory_requirement"]

    months = [1, 2, 3]

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=months)

    model.buy = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def purchase_rule(mdl, t):
        return purchase_price[t - 1]
    model.purchase_price = pyo.Param(model.M, initialize=purchase_rule)

    def selling_rule(mdl, t):
        return selling_price[t - 1]
    model.selling_price = pyo.Param(model.M, initialize=selling_rule)

    # Inventory balance at each month
    def inventory_balance_rule(mdl, t):
        if t == 1:
            return mdl.inventory[t] == initial_inventory + mdl.buy[t] - mdl.sell[t]
        return mdl.inventory[t] == mdl.inventory[t - 1] + mdl.buy[t] - mdl.sell[t]
    model.inventory_balance = pyo.Constraint(model.M, rule=inventory_balance_rule)

    # Cash balance at each month
    def cash_balance_rule(mdl, t):
        if t == 1:
            return mdl.cash[t] == initial_funds \
                - mdl.purchase_price[t] * mdl.buy[t] \
                + mdl.selling_price[t] * mdl.sell[t]
        return mdl.cash[t] == mdl.cash[t - 1] \
            - mdl.purchase_price[t] * mdl.buy[t] \
            + mdl.selling_price[t] * mdl.sell[t]
    model.cash_balance = pyo.Constraint(model.M, rule=cash_balance_rule)

    # Storage capacity
    def capacity_rule(mdl, t):
        return mdl.inventory[t] <= warehouse_capacity
    model.capacity = pyo.Constraint(model.M, rule=capacity_rule)

    # Terminal inventory requirement at end of period
    model.terminal_inventory = pyo.Constraint(
        expr=model.inventory[3] == terminal_inventory_requirement
    )

    # Objective: maximize final cash (profit over quarter)
    model.profit = pyo.Expression(expr=model.cash[3])

    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}