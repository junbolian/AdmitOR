import pyomo.environ as pyo


def solve(params):
    demand = params["demand"]                  # 3x4
    initial_inventory = params["initial_inventory"]  # list of 3
    final_inventory = params["final_inventory"]      # list of 3
    cap_hours = params["production_hours_per_quarter"]
    unit_hours = params["unit_hours"]          # list of 3
    comp_cost = params["compensation_cost"]    # list of 3
    store_cost = params["storage_cost"]

    n_prod = 3
    n_q = 4
    products = list(range(n_prod))
    quarters = list(range(n_q))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.Q = pyo.Set(initialize=quarters)

    model.prod = pyo.Var(model.P, model.Q, domain=pyo.NonNegativeReals)
    model.stock = pyo.Var(model.P, model.Q, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.P, model.Q, domain=pyo.NonNegativeReals)

    def stock_prev(i, t):
        return initial_inventory[i] if t == 0 else model.stock[i, t - 1]

    def backlog_prev(i, t):
        return 0.0 if t == 0 else model.backlog[i, t - 1]

    def balance_rule(model, i, t):
        return (stock_prev(i, t) + model.prod[i, t] + model.backlog[i, t]
                == model.stock[i, t] + demand[i][t] + backlog_prev(i, t))

    model.balance = pyo.Constraint(model.P, model.Q, rule=balance_rule)

    # Final inventory requirement
    def final_stock_rule(model, i):
        return model.stock[i, n_q - 1] == final_inventory[i]

    model.final_stock = pyo.Constraint(model.P, rule=final_stock_rule)

    # Product I cannot be produced in quarter 2 (0-indexed: quarter 1)
    def q2_ban_rule(model):
        return model.prod[0, 1] == 0

    model.q2_ban = pyo.Constraint(rule=q2_ban_rule)

    # Capacity per quarter
    def cap_rule(model, t):
        return sum(unit_hours[i] * model.prod[i, t] for i in model.P) <= cap_hours

    model.capacity = pyo.Constraint(model.Q, rule=cap_rule)

    def obj_rule(model):
        comp = sum(comp_cost[i] * model.backlog[i, t]
                   for i in model.P for t in model.Q)
        store = sum(store_cost * model.stock[i, t]
                    for i in model.P for t in model.Q)
        return comp + store

    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    from pyomo.contrib.appsi.solvers.highs import Highs
    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}