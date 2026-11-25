import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [1, 2, 3]
    schools = [1, 2, 3, 4]

    profit = {}
    demand = {}
    for p in products:
        for s in schools:
            profit[(p, s)] = params["profit_p%d_s%d" % (p, s)]
            demand[(p, s)] = params["demand_p%d_s%d" % (p, s)]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.S = pyo.Set(initialize=schools)
    model.PS = pyo.Set(initialize=[(p, s) for p in products for s in schools])

    model.x = pyo.Var(model.PS, within=pyo.Reals)

    def profit_rule(model):
        return sum(profit[(p, s)] * model.x[(p, s)] for p in model.P for s in model.S)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def demand_rule(model, p, s):
        return model.x[(p, s)] == demand[(p, s)]

    model.demand_con = pyo.Constraint(model.PS, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}