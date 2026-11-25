import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    n_companies = len(profit)
    n_markets = len(profit[0])

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_companies - 1)
    model.J = pyo.RangeSet(0, n_markets - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}