import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price = params["price"]
    share_limit = params["share_limit"]
    payoff = params["payoff"]

    num_sec = len(price)
    num_out = len(payoff[0])

    model = pyo.ConcreteModel()

    model.sec = pyo.RangeSet(1, num_sec)
    model.out = pyo.RangeSet(1, num_out)

    model.x = pyo.Var(model.sec, domain=pyo.NonNegativeReals)

    model.revenue = pyo.Var(model.out, domain=pyo.Reals)

    def revenue_rule(mdl, o):
        return mdl.revenue[o] == sum(payoff[s - 1][o - 1] * mdl.x[s] for s in mdl.sec)
    model.revenue_con = pyo.Constraint(model.out, rule=revenue_rule)

    def limit_rule(mdl, s):
        return mdl.x[s] <= share_limit[s - 1]
    model.limit_con = pyo.Constraint(model.sec, rule=limit_rule)

    model.worst = pyo.Var(domain=pyo.Reals)

    def worst_rule(mdl, o):
        return mdl.worst <= mdl.revenue[o]
    model.worst_con = pyo.Constraint(model.out, rule=worst_rule)

    def obj_rule(mdl):
        cost = sum(price[s - 1] * mdl.x[s] for s in mdl.sec)
        return mdl.worst - cost
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {'objective': obj_val, 'status': 'optimal'}