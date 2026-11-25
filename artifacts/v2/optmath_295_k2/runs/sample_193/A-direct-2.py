import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    origins = range(4)
    dests = range(5)
    products = range(2)

    supply = {}
    for o in origins:
        for p in products:
            supply[(o, p)] = params[f"supply_origin{o}_product{p}"]

    demand = {}
    for d in dests:
        for p in products:
            demand[(d, p)] = params[f"demand_dest{d}_product{p}"]

    cost = params["cost_matrix"]
    capacity = params["capacity_matrix"]

    model = pyo.ConcreteModel()

    model.O = pyo.Set(initialize=list(origins))
    model.D = pyo.Set(initialize=list(dests))
    model.P = pyo.Set(initialize=list(products))

    model.x = pyo.Var(model.O, model.D, model.P, within=pyo.NonNegativeReals)

    def eq_rule(model, o, p):
        return sum(model.x[o, d, p] for d in model.D) == supply[(o, p)]
    model.supply_cons = pyo.Constraint(model.O, model.P, rule=eq_rule)

    def dem_rule(model, d, p):
        return sum(model.x[o, d, p] for o in model.O) == demand[(d, p)]
    model.demand_cons = pyo.Constraint(model.D, model.P, rule=dem_rule)

    def cap_rule(model, o, d):
        return sum(model.x[o, d, p] for p in model.P) <= capacity[o][d]
    model.cap_cons = pyo.Constraint(model.O, model.D, rule=cap_rule)

    def obj_rule(model):
        return sum(cost[o][d][p] * model.x[o, d, p]
                   for o in model.O for d in model.D for p in model.P)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}