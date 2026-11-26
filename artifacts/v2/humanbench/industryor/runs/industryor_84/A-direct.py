import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    raw_cost = {
        'A': params["raw_cost_A"],
        'B': params["raw_cost_B"],
        'C': params["raw_cost_C"],
    }
    limit = {
        'A': params["limit_A"],
        'B': params["limit_B"],
        'C': params["limit_C"],
    }
    proc_fee = {
        1: params["proc_fee_1"],
        2: params["proc_fee_2"],
        3: params["proc_fee_3"],
    }
    price = {
        1: params["price_1"],
        2: params["price_2"],
        3: params["price_3"],
    }
    content_A_min_1 = params["content_A_min_1"]
    content_B_min_2 = params["content_B_min_2"]
    content_C_max_1 = params["content_C_max_1"]
    content_C_max_2 = params["content_C_max_2"]
    content_C_max_3 = params["content_C_max_3"]

    candies = [1, 2, 3]
    raws = ['A', 'B', 'C']

    model = pyo.ConcreteModel()

    # x[c] = total production of candy type c (kg)
    model.x = pyo.Var(candies, within=pyo.NonNegativeReals)
    # y[r, c] = amount of raw material r used in candy type c (kg)
    model.y = pyo.Var(raws, candies, within=pyo.NonNegativeReals)

    # Mass balance: sum of raw materials in candy c equals total production of c
    def mass_balance_rule(model, c):
        return sum(model.y[r, c] for r in raws) == model.x[c]
    model.mass_balance = pyo.Constraint(candies, rule=mass_balance_rule)

    # Raw material monthly limits
    def limit_rule(model, r):
        return sum(model.y[r, c] for c in candies) <= limit[r]
    model.raw_limit = pyo.Constraint(raws, rule=limit_rule)

    # Content constraints
    model.cons_A_min_1 = pyo.Constraint(
        expr=model.y['A', 1] >= content_A_min_1 * model.x[1])
    model.cons_B_min_2 = pyo.Constraint(
        expr=model.y['B', 2] >= content_B_min_2 * model.x[2])
    model.cons_C_max_1 = pyo.Constraint(
        expr=model.y['C', 1] <= content_C_max_1 * model.x[1])
    model.cons_C_max_2 = pyo.Constraint(
        expr=model.y['C', 2] <= content_C_max_2 * model.x[2])
    model.cons_C_max_3 = pyo.Constraint(
        expr=model.y['C', 3] <= content_C_max_3 * model.x[3])

    # Objective: maximize profit = revenue - raw material cost - processing fee
    def obj_rule(model):
        revenue = sum(price[c] * model.x[c] for c in candies)
        raw_cost_total = sum(raw_cost[r] * model.y[r, c] for r in raws for c in candies)
        proc_cost_total = sum(proc_fee[c] * model.x[c] for c in candies)
        return revenue - raw_cost_total - proc_cost_total
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {'objective': obj_val, 'status': 'optimal'}