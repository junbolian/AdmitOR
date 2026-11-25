import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]          # demand[market][product]
    profit_c0 = params["profit_c0"]    # profit_c0[market][product]
    profit_c1 = params["profit_c1"]    # profit_c1[market][product]

    markets = range(len(demand))
    products = range(len(demand[0]))
    companies = range(2)

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=list(markets))
    model.P = pyo.Set(initialize=list(products))
    model.C = pyo.Set(initialize=list(companies))

    def profit_coef(c, mk, pr):
        if c == 0:
            return profit_c0[mk][pr]
        return profit_c1[mk][pr]

    model.x = pyo.Var(model.C, model.M, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit_coef(c, mk, pr) * m.x[c, mk, pr]
                   for c in m.C for mk in m.M for pr in m.P)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, mk, pr):
        return sum(m.x[c, mk, pr] for c in m.C) == demand[mk][pr]

    model.demand_con = pyo.Constraint(model.M, model.P, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}