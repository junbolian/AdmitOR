import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    lots = ['W0', 'W1', 'W2', 'W3']
    layers = ['L0', 'L1', 'L2']

    # Each param is a per-layer list [L0, L1, L2]
    p = {
        'W0': [float(x) for x in params["processing_time_W0"]],
        'W1': [float(x) for x in params["processing_time_W1"]],
        'W2': [float(x) for x in params["processing_time_W2"]],
        'W3': [float(x) for x in params["processing_time_W3"]],
    }

    n = len(lots)
    M = 1e5

    model = pyo.ConcreteModel()
    model.LOTS = pyo.Set(initialize=lots, ordered=True)
    model.LAYERS = pyo.Set(initialize=layers, ordered=True)

    # Pairwise ordering: before[i,j] == 1 iff lot i precedes lot j
    model.before = pyo.Var(model.LOTS, model.LOTS, domain=pyo.Binary)

    # Antisymmetry: for i != j, before[i,j] + before[j,i] == 1
    def order_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return model.before[i, j] + model.before[j, i] == 1
    model.order_con = pyo.Constraint(model.LOTS, model.LOTS, rule=order_rule)

    # Transitivity: before[i,j] + before[j,k] - before[i,k] <= 1
    def trans_rule(model, i, j, k):
        if i == j or j == k or i == k:
            return pyo.Constraint.Skip
        return model.before[i, j] + model.before[j, k] - model.before[i, k] <= 1
    model.trans_con = pyo.Constraint(model.LOTS, model.LOTS, model.LOTS, rule=trans_rule)

    # Start time of each lot at each layer
    model.start = pyo.Var(model.LOTS, model.LAYERS, domain=pyo.NonNegativeReals)

    # Makespan variable (cycle time)
    model.cycle = pyo.Var(domain=pyo.NonNegativeReals)

    # Completion of last layer <= cycle
    model.cycle_def = pyo.Constraint(
        model.LOTS,
        rule=lambda model, j: model.start[j, 'L2'] + p[j][2] <= model.cycle
    )

    # Within-lot precedence: layer k+1 starts after layer k completes
    def within_rule(model, j, k):
        return model.start[j, layers[k + 1]] >= model.start[j, layers[k]] + p[j][k]
    model.within_con = pyo.Constraint(
        model.LOTS, [0, 1], rule=within_rule
    )

    # No-overlap at each layer, following the fixed sequence
    def no_overlap_rule(model, i, j, li):
        if i == j:
            return pyo.Constraint.Skip
        ly = layers[li]
        return model.start[j, ly] >= model.start[i, ly] + p[i][li] - M * (1 - model.before[i, j])
    model.no_overlap_con = pyo.Constraint(
        model.LOTS, model.LOTS, [0, 1, 2], rule=no_overlap_rule
    )

    model.obj = pyo.Objective(expr=model.cycle, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}