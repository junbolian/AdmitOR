import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n_batches = 3
    n_stations = 3

    pt = {}
    for i in range(n_batches):
        for j in range(n_stations):
            pt[(i, j)] = params[f"pt_{i}_{j}"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, n_batches - 1)
    model.J = pyo.RangeSet(0, n_stations - 1)
    model.P = pyo.Set(initialize=list(range(n_batches)), ordered=True)

    # Big-M
    horizon = sum(pt[(i, j)] for i in range(n_batches) for j in range(n_stations))
    big_m = horizon

    model.start = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)
    model.comp = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Precedence within a batch across stations
    model.precedence = pyo.ConstraintList()
    for i in model.I:
        for j in model.J:
            if j >= 1:
                model.precedence.add(
                    model.start[i, j] >= model.comp[i, j - 1]
                )

    # Completion definition
    model.completion = pyo.ConstraintList()
    for i in model.I:
        for j in model.J:
            model.completion.add(
                model.comp[i, j] == model.start[i, j] + pt[(i, j)]
            )

    # Machine sequencing via disjunctive constraints (big-M)
    model.seq = pyo.ConstraintList()
    pairs = [(a, b) for a in range(n_batches) for b in range(a + 1, n_batches)]

    model.y = pyo.Var(
        pairs, model.J, within=pyo.Binary, initialize=0
    )

    for j in model.J:
        for (a, b) in pairs:
            # If y=1: a before b on station j
            # If y=0: b before a
            model.seq.add(
                model.start[b, j] >= model.comp[a, j] - big_m * (1 - model.y[a, b, j])
            )
            model.seq.add(
                model.start[a, j] >= model.comp[b, j] - big_m * model.y[a, b, j]
            )

    # Makespan constraint
    model.makespan_def = pyo.ConstraintList()
    for i in model.I:
        model.makespan_def.add(model.makespan >= model.comp[i, n_stations - 1])

    # Objective
    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}