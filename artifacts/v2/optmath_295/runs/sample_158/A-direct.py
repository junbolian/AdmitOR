import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    n_comp = len(profit)
    n_mkt = len(profit[0])
    n_prod = len(profit[0][0])

    comps = list(range(n_comp))
    mkts = list(range(n_mkt))
    prods = list(range(n_prod))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(comps, mkts, prods, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            profit[c][k][p] * mdl.x[c, k, p]
            for c in comps for k in mkts for p in prods
        )
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(mdl, k, p):
        return sum(mdl.x[c, k, p] for c in comps) == demand[k][p]
    model.demand_con = pyo.Constraint(mkts, prods, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}