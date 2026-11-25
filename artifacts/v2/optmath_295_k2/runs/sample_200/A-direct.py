import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = [0, 1, 2]
    ops = [0, 1]

    pt = {
        (0, 0): params["processing_time_j0_o0"],
        (0, 1): params["processing_time_j0_o1"],
        (1, 0): params["processing_time_j1_o0"],
        (1, 1): params["processing_time_j1_o1"],
        (2, 0): params["processing_time_j2_o0"],
        (2, 1): params["processing_time_j2_o1"],
    }
    lag = {
        0: params["precedence_lag_j0"],
        1: params["precedence_lag_j1"],
        2: params["precedence_lag_j2"],
    }
    bigM = params["machine_disjunctive_bigM"]

    all_ops = [(j, o) for j in jobs for o in ops]

    model = pyo.ConcreteModel()

    model.START_INDEX = pyo.Set(initialize=all_ops)
    model.start = pyo.Var(model.START_INDEX, domain=pyo.NonNegativeReals)

    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    # Unordered pairs of distinct operations
    pairs = []
    for a in range(len(all_ops)):
        for b in range(a + 1, len(all_ops)):
            pairs.append((all_ops[a], all_ops[b]))

    model.PAIR_INDEX = pyo.Set(initialize=pairs, dimen=4)
    model.order = pyo.Var(model.PAIR_INDEX, domain=pyo.Binary)

    # Precedence constraints
    model.prec = pyo.ConstraintList()
    for j in jobs:
        model.prec.add(
            model.start[j, 1] >= model.start[j, 0] + pt[(j, 0)] + lag[j]
        )

    # Machine disjunctive constraints (two separate constraint lists)
    model.disj1 = pyo.Constraint(model.PAIR_INDEX)
    model.disj2 = pyo.Constraint(model.PAIR_INDEX)

    for (ja, oa), (jb, ob) in pairs:
        model.disj1[ja, oa, jb, ob] = (
            model.start[jb, ob]
            >= model.start[ja, oa]
            + pt[(ja, oa)]
            - bigM * (1 - model.order[ja, oa, jb, ob])
        )
        model.disj2[ja, oa, jb, ob] = (
            model.start[ja, oa]
            >= model.start[jb, ob]
            + pt[(jb, ob)]
            - bigM * model.order[ja, oa, jb, ob]
        )

    # Makespan constraints
    model.ms = pyo.ConstraintList()
    for j in jobs:
        for o in ops:
            model.ms.add(model.makespan >= model.start[j, o] + pt[(j, o)])

    # Objective
    model.objective_expr = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    # Solve with HiGHS
    Highs().solve(model)

    obj_val = float(pyo.value(model.objective_expr))
    return {"objective": obj_val, "status": "optimal"}