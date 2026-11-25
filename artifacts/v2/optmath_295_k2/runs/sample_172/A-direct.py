import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1, 2]
    periods = [0, 1, 2, 3, 4]

    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost"]
    hours_grinders = params["machine_hours_grinders"]
    hours_drills = params["machine_hours_drills"]
    hours_borers = params["machine_hours_borers"]
    req_grinders = params["time_req_grinders"]
    req_drills = params["time_req_drills"]
    req_borers = params["time_req_borers"]
    inv_cap = params["inventory_capacity"]
    sales_lim = {
        0: params["sales_limit_p0"],
        1: params["sales_limit_p1"],
        2: params["sales_limit_p2"],
    }
    target_inv = params["target_inventory"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[j] * m.sale[j, t] for j in m.P for t in m.T
        ) - sum(
            hold_cost * m.inv[j, t] for j in m.P for t in m.T
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance (period 0 uses zero initial inventory)
    def balance_rule(m, j, t):
        if t == 0:
            return m.prod[j, t] == m.sale[j, t] + m.inv[j, t]
        return m.inv[j, t - 1] + m.prod[j, t] == m.sale[j, t] + m.inv[j, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Machine capacity constraints
    def grinder_rule(m, t):
        return sum(req_grinders[j] * m.prod[j, t] for j in m.P) <= hours_grinders[t]

    def drill_rule(m, t):
        return sum(req_drills[j] * m.prod[j, t] for j in m.P) <= hours_drills[t]

    def borer_rule(m, t):
        return sum(req_borers[j] * m.prod[j, t] for j in m.P) <= hours_borers[t]

    model.cap_grinders = pyo.Constraint(model.T, rule=grinder_rule)
    model.cap_drills = pyo.Constraint(model.T, rule=drill_rule)
    model.cap_borers = pyo.Constraint(model.T, rule=borer_rule)

    # Inventory capacity
    def inv_cap_rule(m, j, t):
        return m.inv[j, t] <= inv_cap

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    # Sales limits
    def sales_rule(m, j, t):
        return m.sale[j, t] <= sales_lim[j][t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_rule)

    # Target ending inventory (period 4)
    def target_rule(m, j):
        return m.inv[j, 4] == target_inv

    model.target = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}