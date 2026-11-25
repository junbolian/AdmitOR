import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = 4
    n_dest = 5
    n_prod = 2

    origins = range(n_orig)
    dests = range(n_dest)
    prods = range(n_prod)

    def sup(o, p):
        return supply[o * n_prod + p]

    def dem(d, p):
        return demand[d * n_prod + p]

    def cst(o, d, p):
        return cost[(o * n_dest + d) * n_prod + p]

    def cap(o, d):
        return capacity[o * n_dest + d]

    model = pyo.ConcreteModel()

    model.O = pyo.Set(initialize=list(origins))
    model.D = pyo.Set(initialize=list(dests))
    model.P = pyo.Set(initialize=list(prods))

    model.x = pyo.Var(model.O, model.D, model.P, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, o, p):
        return sum(mdl.x[o, d, p] for d in mdl.D) == sup(o, p)
    model.supply_con = pyo.Constraint(model.O, model.P, rule=supply_rule)

    def demand_rule(mdl, d, p):
        return sum(mdl.x[o, d, p] for o in mdl.O) == dem(d, p)
    model.demand_con = pyo.Constraint(model.D, model.P, rule=demand_rule)

    def cap_rule(mdl, o, d):
        return sum(mdl.x[o, d, p] for p in mdl.P) <= cap(o, d)
    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    def obj_rule(mdl):
        return sum(cst(o, d, p) * mdl.x[o, d, p]
                   for o in mdl.O for d in mdl.D for p in mdl.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}