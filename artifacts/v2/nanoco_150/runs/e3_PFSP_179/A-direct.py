import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_times"]
    n = 4  # number of batches
    m = 3  # number of stages

    batches = list(range(n))
    stages = list(range(m))

    model = pyo.ConcreteModel()

    # x[i, k] = 1 if batch i is at position k in the sequence
    model.x = pyo.Var(batches, batches, domain=pyo.Binary)

    # each batch assigned to exactly one position
    model.pos_of = pyo.Constraint(
        batches, rule=lambda mdl, i: sum(mdl.x[i, k] for k in batches) == 1
    )
    # each position gets exactly one batch
    model.batch_at = pyo.Constraint(
        batches, rule=lambda mdl, k: sum(mdl.x[i, k] for i in batches) == 1
    )

    bigM = sum(pt[i][j] for i in batches for j in stages) + 1

    model.start = pyo.Var(batches, stages, domain=pyo.NonNegativeReals)
    model.comp = pyo.Var(batches, stages, domain=pyo.NonNegativeReals)

    model.proc = pyo.Constraint(
        batches,
        stages,
        rule=lambda mdl, i, j: mdl.comp[i, j] == mdl.start[i, j] + pt[i][j],
    )

    # Same batch flow: stage j+1 starts after stage j completes
    model.flow = pyo.Constraint(
        batches,
        stages[:-1],
        rule=lambda mdl, i, j: mdl.start[i, j + 1] >= mdl.comp[i, j],
    )

    # Precedence between consecutive positions on each stage
    def prec_rule(mdl, i, i2, k, j):
        if k + 1 < n:
            return mdl.start[i2, j] - mdl.comp[i, j] >= -bigM * (
                2 - mdl.x[i, k] - mdl.x[i2, k + 1]
            )
        return pyo.Constraint.Skip

    model.prec = pyo.Constraint(batches, batches, batches, stages, rule=prec_rule)

    # Makespan
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)
    model.mk = pyo.Constraint(
        batches, rule=lambda mdl, i: mdl.Cmax >= mdl.comp[i, stages[-1]]
    )

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}