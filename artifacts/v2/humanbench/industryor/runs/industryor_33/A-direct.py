import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["warehouse_capacity"]
    init_stock = params["initial_stock"]
    init_capital = params["initial_capital"]
    buy_price = params["purchase_price"]
    sell_price = params["selling_price"]
    terminal_stock = params["terminal_stock_requirement"]

    months = [1, 2, 3]

    model = pyo.ConcreteModel()
    model.M = pyo.Set(initialize=months)

    # Indexing choice: variables indexed by real month numbers (1,2,3)
    model.buy = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.stock = pyo.Var(model.M, within=pyo.NonNegativeReals)
    model.capital = pyo.Var(model.M, within=pyo.NonNegativeReals)

    def buy_p(m):
        return buy_price[m - 1]

    def sell_p(m):
        return sell_price[m - 1]

    def prev_stock(m):
        return init_stock if m == 1 else model.stock[m - 1]

    def prev_capital(m):
        return init_capital if m == 1 else model.capital[m - 1]

    def stock_balance_rule(m):
        return model.stock[m] == prev_stock(m) + model.buy[m] - model.sell[m]

    model.stock_balance_con = pyo.Constraint(model.M, rule=stock_balance_rule)

    def cap_rule(m):
        return model.stock[m] <= capacity

    model.cap_con = pyo.Constraint(model.M, rule=cap_rule)

    # Grain bought this month cannot be sold this month
    def sell_limit_rule(m):
        return model.sell[m] <= prev_stock(m)

    model.sell_limit_con = pyo.Constraint(model.M, rule=sell_limit_rule)

    def cash_balance_rule(m):
        return model.capital[m] == prev_capital(m) - buy_p(m) * model.buy[m] \
            + sell_p(m) * model.sell[m]

    model.cash_balance_con = pyo.Constraint(model.M, rule=cash_balance_rule)

    # Pay on delivery: cannot spend more than available cash this month
    def cash_limit_rule(m):
        return buy_p(m) * model.buy[m] <= prev_capital(m) + sell_p(m) * model.sell[m]

    model.cash_limit_con = pyo.Constraint(model.M, rule=cash_limit_rule)

    model.terminal_con = pyo.Constraint(expr=model.stock[3] == terminal_stock)

    def obj_rule(m):
        return m.capital[3]

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}