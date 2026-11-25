import pyomo.environ as pyo


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    n_companies = len(profit)
    n_products = len(profit[0])
    n_markets = len(profit[0][0])

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, n_companies - 1)
    model.P = pyo.RangeSet(0, n_products - 1)
    model.M = pyo.RangeSet(0, n_markets - 1)

    model.x = pyo.Var(model.C, model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[c][p][mk] * m.x[c, p, mk]
            for c in m.C
            for p in m.P
            for mk in m.M
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, p, mk):
        return sum(m.x[c, p, mk] for c in m.C) == demand[mk][p]

    model.demand_con = pyo.Constraint(model.P, model.M, rule=demand_rule)

    from pyomo.contrib.appsi.solvers.highs import Highs
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}