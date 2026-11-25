import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proc_time = params["proc_time"]
    batches = list(range(len(proc_time)))       # 0..3
    units = list(range(len(proc_time[0])))      # 0..2

    # Big-M for sequencing on the first unit
    total_time = sum(proc_time[i][u] for i in batches for u in units)

    model = pyo.ConcreteModel()

    model.B = pyo.Set(initialize=batches)
    model.U = pyo.Set(initialize=units)

    # Completion time of batch i at unit u
    model.C = pyo.Var(model.B, model.U, within=pyo.NonNegativeReals)

    # Makespan
    model.T = pyo.Var(within=pyo.NonNegativeReals)

    # Position of batch i in the permutation (0-based), via disjunctive y_{i,j}
    model.y = pyo.Var(model.B, model.B, within=pyo.Binary)

    # y[i,j] = 1 means i precedes j in the sequence
    for i in model.B:
        for j in model.B:
            if i < j:
                model.y[i, j] + model.y[j, i] == 1

    # No-overlap on each unit (permutation flow shop)
    for u in model.U:
        for i in model.B:
            for j in model.B:
                if i != j:
                    model.y[i, j] * total_time + model.C[j, u] >= model.C[i, u] + proc_time[j][u]

    # Precedence within each job: DAG on units 0 -> 1 -> 2
    for i in model.B:
        for u in model.U:
            if u < len(units) - 1:
                model.C[i, u + 1] >= model.C[i, u] + proc_time[i][u + 1]

    # Makespan definition
    for i in model.B:
        model.T >= model.C[i, units[-1]]

    model.obj = pyo.Objective(expr=model.T, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}