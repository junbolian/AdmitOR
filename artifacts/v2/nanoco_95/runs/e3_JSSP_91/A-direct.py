import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_times"]

    lots = ["L0", "L1", "L2"]
    machines = [0, 1, 2]
    routing = {lot: [1, 0, 2] for lot in lots}
    steps = [0, 1, 2]

    model = pyo.ConcreteModel()

    model.LOTS = pyo.Set(initialize=lots)
    model.MACHINES = pyo.Set(initialize=machines)
    model.STEPS = pyo.Set(initialize=steps)

    model.LOT_STEP = pyo.Set(
        initialize=[(l, s) for l in lots for s in steps], dimen=2
    )

    model.start = pyo.Var(model.LOT_STEP, within=pyo.NonNegativeReals)
    model.C = pyo.Var(within=pyo.NonNegativeReals)

    def ptime_rule(model, l, s):
        mach = routing[l][s]
        row = lots.index(l)
        return float(pt[row][mach])

    model.p = pyo.Param(model.LOT_STEP, initialize=ptime_rule)

    def prec_rule(model, l, s):
        if s < 2:
            return model.start[l, s + 1] >= model.start[l, s] + model.p[l, s]
        return pyo.Constraint.Skip

    model.prec = pyo.Constraint(model.LOT_STEP, rule=prec_rule)

    def makespan_rule(model, l):
        return model.C >= model.start[l, 2] + model.p[l, 2]

    model.makespan = pyo.Constraint(model.LOTS, rule=makespan_rule)

    pair_list = [
        ((l1, s1), (l2, s2))
        for l1 in lots
        for s1 in steps
        for l2 in lots
        for s2 in steps
        if (l1, s1) < (l2, s2) and routing[l1][s1] == routing[l2][s2]
    ]

    model.PAIR_A = pyo.Set(
        initialize=[(a, b) for a, b in pair_list], dimen=4
    ) if False else None  # placeholder avoided

    # Use flat indexed binary variable with explicit pair index via RangeSet
    model.PAIRS = pyo.RangeSet(0, len(pair_list) - 1)
    model.y = pyo.Var(model.PAIRS, within=pyo.Binary)

    bigM = 100000

    def disj1_rule(model, k):
        a, b = pair_list[k]
        return model.start[a] + model.p[a] <= model.start[b] + bigM * (1 - model.y[k])

    def disj2_rule(model, k):
        a, b = pair_list[k]
        return model.start[b] + model.p[b] <= model.start[a] + bigM * model.y[k]

    model.disj1 = pyo.Constraint(model.PAIRS, rule=disj1_rule)
    model.disj2 = pyo.Constraint(model.PAIRS, rule=disj2_rule)

    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}