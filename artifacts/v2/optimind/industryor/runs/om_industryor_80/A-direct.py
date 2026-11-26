import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    types = ["jewelry", "shoes&hats", "general", "bookstore", "catering"]
    area = params["area"]
    min_shops = params["min_shops"]
    max_shops = params["max_shops"]
    profit_1 = params["profit_1"]
    profit_2 = params["profit_2"]
    profit_3 = params["profit_3"]
    rent_rate = params["rent_rate"]
    space_capacity = params["space_capacity"]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=types, ordered=True)
    model.K = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.x = pyo.Var(model.T, domain=pyo.NonNegativeIntegers, bounds=(0, 3))
    model.z = pyo.Var(model.T, model.K, domain=pyo.Binary)

    def profit_for(m, t, k):
        if k == 1:
            return profit_1[t]
        elif k == 2:
            return profit_2[t]
        else:
            return profit_3[t]

    # For each type/k, determine whether k is allowed
    allowed = {}
    for t in types:
        for k in model.K:
            pk = profit_for(model, t, k)
            if pk is None or k > max_shops[t]:
                allowed[(t, k)] = False
            else:
                allowed[(t, k)] = True

    # Fix disallowed z to zero
    for t in types:
        for k in model.K:
            if not allowed[(t, k)]:
                model.z[t, k].fix(0)

    # at most one k selected per type (k=0 via all zero -> x=0)
    def one_k_rule(m, t):
        return sum(m.z[t, k] for k in m.K) <= 1
    model.one_k = pyo.Constraint(model.T, rule=one_k_rule)

    # x[t] = sum_k k*z[t,k]
    def xlink_rule(m, t):
        return m.x[t] == sum(k * m.z[t, k] for k in m.K)
    model.xlink = pyo.Constraint(model.T, rule=xlink_rule)

    # min/max shops
    def min_rule(m, t):
        return m.x[t] >= min_shops[t]
    model.min_c = pyo.Constraint(model.T, rule=min_rule)

    def max_rule(m, t):
        return m.x[t] <= max_shops[t]
    model.max_c = pyo.Constraint(model.T, rule=max_rule)

    # space constraint
    def space_rule(m):
        return sum(area[t] * m.x[t] for t in m.T) <= space_capacity
    model.space = pyo.Constraint(rule=space_rule)

    # objective: rent = rent_rate * total profit
    def obj_rule(m):
        total = 0
        for t in m.T:
            for k in m.K:
                pk = profit_for(m, t, k)
                if pk is None:
                    continue
                total = total + k * pk * m.z[t, k]
        return rent_rate * total
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}