import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit_margin = params["profit_margin"]

    markets = list(range(len(demand)))

    model = pyo.ConcreteModel()

    model.markets = pyo.Set(initialize=markets)

    model.supply = pyo.Var(model.markets, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit_margin[i] * m.supply[i] for i in m.markets)

    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def demand_rule(m, i):
        return m.supply[i] == demand[i]

    model.demand_con = pyo.Constraint(model.markets, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}