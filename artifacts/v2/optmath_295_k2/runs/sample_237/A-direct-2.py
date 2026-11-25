import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    profit_data = params["profit"]      # [company][market][product]
    demand_data = params["demand"]      # [market][product]

    num_companies = len(profit_data)
    num_markets = len(profit_data[0]) if num_companies > 0 else 0
    num_products = len(profit_data[0][0]) if num_markets > 0 else 0

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=range(num_companies))
    model.M = pyo.Set(initialize=range(num_markets))
    model.P = pyo.Set(initialize=range(num_products))

    model.x = pyo.Var(model.C, model.M, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(model):
        return sum(
            profit_data[c][m][p] * model.x[c, m, p]
            for c in model.C
            for m in model.M
            for p in model.P
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(model, m, p):
        return sum(model.x[c, m, p] for c in model.C) == demand_data[m][p]
    model.demand_constraint = pyo.Constraint(model.M, model.P, rule=demand_rule)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or solver failed"}

    return {"objective": obj_val, "status": "optimal"}