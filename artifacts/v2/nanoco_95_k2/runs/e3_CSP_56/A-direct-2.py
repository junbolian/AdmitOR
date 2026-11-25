import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    L = params["standard_rebar_length"]
    pieces = [params["piece_length_18"], params["piece_length_20"], params["piece_length_56"]]
    demands = [params["demand_18"], params["demand_20"], params["demand_56"]]
    n = 3

    max_counts = [[L // pieces[i] for i in range(n)] for _ in range(n)]

    patterns = []
    for a in range(max_counts[0][0] + 1):
        for b in range(max_counts[1][1] + 1):
            for c in range(max_counts[2][2] + 1):
                if (a * pieces[0] + b * pieces[1] + c * pieces[2]) <= L:
                    patterns.append((a, b, c))

    npat = len(patterns)
    M = sum(demands)

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, npat - 1)
    model.T = pyo.RangeSet(0, n - 1)
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=(0, M))

    def obj_rule(mdl):
        return sum(mdl.x[p] for p in mdl.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def dem_rule(mdl, t):
        return sum(mdl.x[p] * patterns[p][t] for p in mdl.P) >= demands[t]
    model.dem = pyo.Constraint(model.T, rule=dem_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}