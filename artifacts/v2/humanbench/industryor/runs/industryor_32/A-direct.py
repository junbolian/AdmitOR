def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_prices = params["purchase_prices"]
    sale_prices = params["sale_prices"]

    n_months = len(purchase_prices)
    months = list(range(n_months))
    last = n_months - 1

    model = pyo.ConcreteModel()
    model.months = pyo.Set(initialize=months)

    model.purchase = pyo.Var(model.months, within=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.months, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, within=pyo.NonNegativeReals)

    def inventory_balance_rule(mdl, t):
        if t == 0:
            return mdl.inventory[t] == initial_inventory + mdl.purchase[t] - mdl.sale[t]
        return mdl.inventory[t] == mdl.inventory[t - 1] + mdl.purchase[t] - mdl.sale[t]

    model.inventory_balance = pyo.Constraint(model.months, rule=inventory_balance_rule)

    def capacity_rule(mdl, t):
        return mdl.inventory[t] <= capacity

    model.capacity_limit = pyo.Constraint(model.months, rule=capacity_rule)

    def ending_rule(mdl):
        return mdl.inventory[last] == 0

    model.ending_inventory = pyo.Constraint(rule=ending_rule)

    def objective_rule(mdl):
        return sum(sale_prices[t] * mdl.sale[t] - purchase_prices[t] * mdl.purchase[t] for t in mdl.months)

    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))

    return {"objective": obj_val, "status": "optimal"}