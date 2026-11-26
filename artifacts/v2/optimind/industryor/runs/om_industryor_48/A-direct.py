import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    buy_price = params["buy_price"]
    sell_price = params["sell_price"]
    capacity = params["warehouse_capacity"]
    initial_stock = params["initial_stock"]

    months = list(range(6))

    model = pyo.ConcreteModel()
    model.M = pyo.Set(initialize=months)

    model.buy = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def inv_rule(mdl, t):
        prev = initial_stock if t == 0 else mdl.inv[t - 1]
        return mdl.inv[t] == prev + mdl.buy[t] - mdl.sell[t]
    model.inv_con = pyo.Constraint(model.M, rule=inv_rule)

    def cap_rule(mdl, t):
        return mdl.inv[t] <= capacity
    model.cap_con = pyo.Constraint(model.M, rule=cap_rule)

    # Final inventory cannot exceed initial stock (prevents buffering beyond horizon)
    model.final_con = pyo.Constraint(expr=model.inv[5] <= initial_stock)

    def obj_rule(mdl):
        return sum(sell_price[t] * mdl.sell[t] - buy_price[t] * mdl.buy[t] for t in mdl.M)
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}