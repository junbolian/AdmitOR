import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    candies = ['A', 'B', 'C']
    rawmats = ['A', 'B', 'C']

    model.x = pyo.Var(candies, domain=pyo.NonNegativeReals)

    content = {
        ('A', 'A'): params["content_A_in_A"],
        ('B', 'A'): params["content_A_in_B"],
        ('C', 'A'): params["content_C_in_A"],
        ('B', 'B'): params["content_C_in_B"],
        ('C', 'C'): params["content_C_in_C"],
    }

    raw_cost = {'A': params["mat_cost_A"], 'B': params["mat_cost_B"], 'C': params["mat_cost_C"]}
    raw_limit = {'A': params["limit_A"], 'B': params["limit_B"], 'C': params["limit_C"]}
    proc_fee = {'A': params["proc_fee_A"], 'B': params["proc_fee_B"], 'C': params["proc_fee_C"]}
    price = {'A': params["price_A"], 'B': params["price_B"], 'C': params["price_C"]}

    model.raw_limit_con = pyo.ConstraintList()
    for r in rawmats:
        expr = 0
        for c in candies:
            frac = content.get((r, c), 0)
            expr += frac * model.x[c]
        model.raw_limit_con.add(expr <= raw_limit[r])

    def obj_rule(m):
        total = 0
        for c in candies:
            revenue = price[c]
            fee = proc_fee[c]
            rawcost = 0
            for r in rawmats:
                frac = content.get((r, c), 0)
                rawcost += frac * raw_cost[r]
            total += (revenue - fee - rawcost) * m.x[c]
        return total

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {'objective': obj_val, 'status': 'optimal'}