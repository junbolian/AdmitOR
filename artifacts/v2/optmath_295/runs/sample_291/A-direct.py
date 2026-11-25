import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    num_companies = 5
    num_markets = 2

    model = pyo.ConcreteModel()

    model.COMPANIES = pyo.RangeSet(0, num_companies - 1)
    model.MARKETS = pyo.RangeSet(0, num_markets - 1)

    model.supply = pyo.Var(model.COMPANIES, model.MARKETS, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            float(profit[i][j]) * mdl.supply[i, j]
            for i in mdl.COMPANIES
            for j in mdl.MARKETS
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(mdl, j):
        return sum(mdl.supply[i, j] for i in mdl.COMPANIES) == float(demand[j])

    model.demand_con = pyo.Constraint(model.MARKETS, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}