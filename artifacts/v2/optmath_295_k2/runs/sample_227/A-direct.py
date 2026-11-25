import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [1, 2, 3]
    schools = [1, 2, 3, 4]

    profit = {}
    demand = {}
    for s in schools:
        for p in products:
            profit[p, s] = params["profit_p%d_s%d" % (p, s)]
            demand[p, s] = params["demand_p%d_s%d" % (p, s)]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.S = pyo.Set(initialize=schools)

    model.x = pyo.Var(model.P, model.S, domain=pyo.Reals)

    def obj_rule(m):
        return sum(profit[p, s] * m.x[p, s] for p in m.P for s in m.S)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, p, s):
        return m.x[p, s] == demand[p, s]

    model.demand_con = pyo.Constraint(model.P, model.S, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}