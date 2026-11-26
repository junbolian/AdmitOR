import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    num_batches = len(processing_times)
    num_vats = len(processing_times[0])
    big_M = float(sum(sum(row) for row in processing_times)) + 1.0

    batches = list(range(num_batches))
    vats = list(range(num_vats))

    model = pyo.ConcreteModel()

    # Completion time of batch i in vat j
    model.w = pyo.Var(batches, vats, within=pyo.NonNegativeReals)
    # Makespan
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)
    # Binary: x[i,k,j] = 1 if batch i precedes batch k on vat j
    model.x = pyo.Var(
        [(i, k, j) for i in batches for k in batches for j in vats if i != k],
        within=pyo.Binary,
    )

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    model.cons = pyo.ConstraintList()

    # Flow shop precedence: batch i must finish vat j before starting vat j+1
    for i in batches:
        for j in range(1, num_vats):
            model.cons.add(
                model.w[i, j]
                >= model.w[i, j - 1] + processing_times[i][j]
            )

    # First vat: w[i,0] >= p[i][0]
    for i in batches:
        model.cons.add(model.w[i, 0] >= processing_times[i][0])

    # Disjunctive constraints for each vat and each unordered pair
    for j in vats:
        for i in batches:
            for k in batches:
                if i < k:
                    model.cons.add(
                        model.w[k, j]
                        >= model.w[i, j]
                        + processing_times[k][j]
                        - big_M * (1 - model.x[i, k, j])
                    )
                    model.cons.add(
                        model.w[i, j]
                        >= model.w[k, j]
                        + processing_times[i][j]
                        - big_M * model.x[i, k, j]
                    )

    # Makespan
    for i in batches:
        model.cons.add(model.Cmax >= model.w[i, num_vats - 1])

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}