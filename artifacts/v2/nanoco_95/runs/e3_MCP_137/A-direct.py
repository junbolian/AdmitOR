import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    durations = params["durations"]
    edges = params["interference_edges"]
    n = len(durations)

    model = pyo.ConcreteModel()

    model.devices = pyo.RangeSet(0, n - 1)

    # Start times (continuous) and makespan
    model.start = pyo.Var(model.devices, within=pyo.NonNegativeReals)
    model.T = pyo.Var(within=pyo.NonNegativeReals)

    # Non-overlap big-M: use a large enough constant based on total duration
    horizon = sum(durations) + 1
    model.M = float(horizon)

    def obj_rule(m):
        return m.T
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Makespan constraints: start_i + duration_i <= T
    def finish_rule(m, i):
        return m.start[i] + durations[i] <= m.T
    model.finish = pyo.Constraint(model.devices, rule=finish_rule)

    # Non-overlap constraints with binary ordering variables
    model.edges = pyo.Set(initialize=[tuple(e) for e in edges], dimen=2)
    model.y = pyo.Var(model.edges, within=pyo.Binary)

    def pair_rule_1(m, i, j):
        # i before j
        return m.start[i] + durations[i] <= m.start[j] + m.M * (1 - m.y[i, j])
    model.pair1 = pyo.Constraint(model.edges, rule=pair_rule_1)

    def pair_rule_2(m, i, j):
        # j before i
        return m.start[j] + durations[j] <= m.start[i] + m.M * m.y[i, j]
    model.pair2 = pyo.Constraint(model.edges, rule=pair_rule_2)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}