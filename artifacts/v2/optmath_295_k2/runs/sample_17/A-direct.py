import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n_patterns = 12
    widths = [1, 2, 3, 4]

    demand = {
        1: params["demand_width_1"],
        2: params["demand_width_2"],
        3: params["demand_width_3"],
        4: params["demand_width_4"],
    }

    usage_limit = {
        p: params[f"usage_limit_{p}"] for p in range(n_patterns)
    }

    yields = {}
    for p in range(n_patterns):
        for w in widths:
            key = f"pattern_{p}_width_{w}"
            yields[(p, w)] = params[key] if key in params else 0

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_patterns - 1)
    model.W = pyo.Set(initialize=widths)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def usage_rule(model, p):
        return model.x[p] <= usage_limit[p]
    model.usage_con = pyo.Constraint(model.P, rule=usage_rule)

    def demand_rule(model, w):
        return sum(yields[(p, w)] * model.x[p] for p in model.P) >= demand[w]
    model.demand_con = pyo.Constraint(model.W, rule=demand_rule)

    model.obj = pyo.Objective(expr=sum(model.x[p] for p in model.P), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}