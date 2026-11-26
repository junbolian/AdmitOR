import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_inventory = params["initial_inventory"]
    warehouse_capacity = params["warehouse_capacity"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]

    months = [1, 2, 3]

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=months)

    model.purchase = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def inv_rule(mdl, t):
        prev = initial_inventory if t == 1 else mdl.inventory[t - 1]
        return mdl.inventory[t] == prev + mdl.purchase[t] - mdl.sell[t]

    model.inv_con = pyo.Constraint(model.M, rule=inv_rule)

    def cap_rule(mdl, t):
        return mdl.inventory[t] <= warehouse_capacity

    model.cap_con = pyo.Constraint(model.M, rule=cap_rule)

    # Sales cannot exceed available inventory (beginning stock + purchases)
    def sell_rule(mdl, t):
        prev = initial_inventory if t == 1 else mdl.inventory[t - 1]
        return mdl.sell[t] <= prev + mdl.purchase[t]

    model.sell_con = pyo.Constraint(model.M, rule=sell_rule)

    # Initial inventory cannot exceed warehouse capacity
    model.init_cap_con = pyo.Constraint(
        expr=initial_inventory <= warehouse_capacity
    )

    # Cannot purchase more than what fits in the warehouse
    def purchase_cap_rule(mdl, t):
        return mdl.purchase[t] <= warehouse_capacity

    model.purchase_cap_con = pyo.Constraint(model.M, rule=purchase_cap_rule)

    def obj_rule(mdl):
        return sum(
            selling_price[t - 1] * mdl.sell[t] - purchase_price[t - 1] * mdl.purchase[t]
            for t in mdl.M
        )

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))

    return {"objective": obj_val, "status": "optimal"}