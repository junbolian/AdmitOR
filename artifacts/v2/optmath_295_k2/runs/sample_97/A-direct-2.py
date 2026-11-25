import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    earliest = params["earliest"]
    latest = params["latest"]
    target = params["target"]
    early_cost = params["early_cost"]
    late_cost = params["late_cost"]
    separation = params["separation"]

    n = len(earliest)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    sep_map = {p: separation[k] for k, p in enumerate(pairs)}
    big_m = 1000.0

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, n - 1)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.t = pyo.Var(model.aircraft, within=pyo.NonNegativeReals)
    model.e = pyo.Var(model.aircraft, within=pyo.NonNegativeReals)
    model.l = pyo.Var(model.aircraft, within=pyo.NonNegativeReals)
    model.z = pyo.Var(model.pairs, within=pyo.Binary)

    def obj_rule(m):
        return sum(
            early_cost[i] * m.e[i] + late_cost[i] * m.l[i]
            for i in m.aircraft
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def window_rule(m, i):
        return pyo.inequality(earliest[i], m.t[i], latest[i])
    model.window = pyo.Constraint(model.aircraft, rule=window_rule)

    def deviation_rule(m, i):
        return m.t[i] - target[i] == m.l[i] - m.e[i]
    model.deviation = pyo.Constraint(model.aircraft, rule=deviation_rule)

    def sep_rule(m, i, j):
        return m.t[j] - m.t[i] >= sep_map[(i, j)] - big_m * (1 - m.z[(i, j)])
    model.sep = pyo.Constraint(model.pairs, rule=sep_rule)

    def sep_rev_rule(m, i, j):
        return m.t[i] - m.t[j] >= sep_map[(i, j)] - big_m * m.z[(i, j)]
    model.sep_rev = pyo.Constraint(model.pairs, rule=sep_rev_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}