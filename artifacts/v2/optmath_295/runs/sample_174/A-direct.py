import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    periods = list(range(4))
    products = [0, 1]

    model.P = pyo.Set(initialize=periods)
    model.J = pyo.Set(initialize=products)

    # Decision variables
    model.prod = pyo.Var(model.J, model.P, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.J, model.P, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.J, model.P, domain=pyo.NonNegativeReals)

    profit = {0: params["profit_product0"], 1: params["profit_product1"]}
    holding = params["holding_cost"]

    grinder_req = {0: params["grinder_req_product0"], 1: params["grinder_req_product1"]}
    drill_req = {0: params["drill_req_product0"], 1: params["drill_req_product1"]}
    borer_req = {0: params["borer_req_product0"], 1: params["borer_req_product1"]}

    grinder_cap = [params["grinder_capacity"], params["grinder_capacity"], 0.0, params["grinder_capacity"]]
    drill_cap = [params["drill_capacity"], params["drill_capacity"], 0.0, params["drill_capacity"]]
    borer_cap = [params["borer_capacity"], params["borer_capacity"], 0.0, params["borer_capacity"]]

    inv_limit = params["inventory_limit"]
    sales_limit = {
        0: list(params["sales_limit_product0"]),
        1: list(params["sales_limit_product1"]),
    }

    target_inv = {0: params["target_inventory_product0"], 1: params["target_inventory_product1"]}

    # Objective
    def obj_rule(m):
        revenue = sum(profit[j] * m.sales[j, t] for j in m.J for t in m.P)
        cost = sum(holding * m.inv[j, t] for j in m.J for t in m.P)
        return revenue - cost

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance
    def balance_rule(m, j, t):
        if t == 0:
            return m.prod[j, t] == m.sales[j, t] + m.inv[j, t]
        return m.inv[j, t - 1] + m.prod[j, t] == m.sales[j, t] + m.inv[j, t]

    model.balance = pyo.Constraint(model.J, model.P, rule=balance_rule)

    # Machine capacity
    def grinder_rule(m, t):
        return sum(grinder_req[j] * m.prod[j, t] for j in m.J) <= grinder_cap[t]

    def drill_rule(m, t):
        return sum(drill_req[j] * m.prod[j, t] for j in m.J) <= drill_cap[t]

    def borer_rule(m, t):
        return sum(borer_req[j] * m.prod[j, t] for j in m.J) <= borer_cap[t]

    model.grinder_cap = pyo.Constraint(model.P, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.P, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.P, rule=borer_rule)

    # Inventory limit
    def invlimit_rule(m, j, t):
        return m.inv[j, t] <= inv_limit

    model.inv_limit = pyo.Constraint(model.J, model.P, rule=invlimit_rule)

    # Sales limit
    def saleslimit_rule(m, j, t):
        return m.sales[j, t] <= sales_limit[j][t]

    model.sales_limit = pyo.Constraint(model.J, model.P, rule=saleslimit_rule)

    # Target ending inventory
    def target_rule(m, j):
        return m.inv[j, 3] == target_inv[j]

    model.target = pyo.Constraint(model.J, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}