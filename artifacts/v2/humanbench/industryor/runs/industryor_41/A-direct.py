import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    products = ['A1', 'A2', 'A3']
    months = ['Jan', 'Feb', 'Mar', 'Apr']

    demand = {
        'A1': params["demand_A1"],
        'A2': params["demand_A2"],
        'A3': params["demand_A3"],
    }
    price = dict(zip(products, params["price"]))
    prod_cost = dict(zip(products, params["production_cost"]))
    act_cost = dict(zip(products, params["activation_cost"]))
    quota = dict(zip(products, params["production_quota"]))
    min_batch = dict(zip(products, params["min_batch_size"]))
    days = dict(zip(months, params["production_days"]))
    stor_cost = dict(zip(products, params["storage_cost"]))
    stor_cap = params["storage_capacity"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=months)

    # Decision variables
    model.prod = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.active_flag = pyo.Var(model.P, model.M, domain=pyo.Binary)
    model.stock = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)

    # Inventory balance
    def balance_rule(model, p, m):
        idx = months.index(m)
        prev_stock = model.stock[p, months[idx - 1]] if idx > 0 else 0
        return model.stock[p, m] == prev_stock + model.prod[p, m] - demand[p][idx]
    model.balance = pyo.Constraint(model.P, model.M, rule=balance_rule)

    # Quota & minimum batch linked to activation
    def quota_rule(model, p, m):
        return model.prod[p, m] <= quota[p] * days[m] * model.active_flag[p, m]
    model.quota_con = pyo.Constraint(model.P, model.M, rule=quota_rule)

    def batch_rule(model, p, m):
        return model.prod[p, m] >= min_batch[p] * days[m] * model.active_flag[p, m]
    model.batch_con = pyo.Constraint(model.P, model.M, rule=batch_rule)

    # Storage capacity
    def storage_rule(model, m):
        return sum(model.stock[p, m] for p in products) <= stor_cap
    model.storage_con = pyo.Constraint(model.M, rule=storage_rule)

    # Revenue objective
    revenue = sum(price[p] * demand[p][i] for p in products for i in range(len(months)))
    storage_total = sum(stor_cost[p] * model.stock[p, m] for p in products for m in months)
    prod_total = sum(prod_cost[p] * model.prod[p, m] for p in products for m in months)
    act_total = sum(act_cost[p] * model.active_flag[p, m] for p in products for m in months)

    model.obj = pyo.Objective(
        expr=revenue - prod_total - act_total - storage_total,
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}