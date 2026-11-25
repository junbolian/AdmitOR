import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    P = 2
    R = 5
    C = 3

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=range(P))
    model.R = pyo.Set(initialize=range(R))
    model.C = pyo.Set(initialize=range(C))
    model.PR = pyo.Set(initialize=[(p, r) for p in range(P) for r in range(R)], dimen=2)

    model.x = pyo.Var(model.C, model.PR, domain=pyo.NonNegativeReals)

    demand = {}
    for r in range(R):
        for p in range(P):
            demand[p, r] = params["demand_product%d_region%d" % (p, r)]

    profit = {}
    for c in range(C):
        for p in range(P):
            for r in range(R):
                profit[c, p, r] = params["profit_company%d_product%d_region%d" % (c, p, r)]

    def demand_rule(mdl, p, r):
        return sum(mdl.x[c, p, r] for c in mdl.C) == demand[p, r]

    model.demand_con = pyo.Constraint(model.PR, rule=demand_rule)

    def obj_rule(mdl):
        return sum(
            profit[c, p, r] * mdl.x[c, p, r]
            for c in mdl.C
            for (p, r) in mdl.PR
        )

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}