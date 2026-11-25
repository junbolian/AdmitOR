import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]

    num_batches = len(processing_time)
    num_stations = len(processing_time[0])

    big_m = float(sum(float(processing_time[i][j])
                      for i in range(num_batches)
                      for j in range(num_stations)))

    model = pyo.ConcreteModel()

    model.BATCH = pyo.RangeSet(0, num_batches - 1)
    model.STN = pyo.RangeSet(0, num_stations - 1)

    model.start = pyo.Var(model.BATCH, model.STN, within=pyo.NonNegativeReals)
    model.finish = pyo.Var(model.BATCH, model.STN, within=pyo.NonNegativeReals)

    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    def finish_rule(mdl, i, j):
        return mdl.finish[i, j] == mdl.start[i, j] + float(processing_time[i][j])
    model.finish_con = pyo.Constraint(model.BATCH, model.STN, rule=finish_rule)

    def sequence_rule(mdl, i, j):
        if j + 1 <= num_stations - 1:
            return mdl.start[i, j + 1] >= mdl.finish[i, j]
        return pyo.Constraint.Skip
    model.seq_con = pyo.Constraint(model.BATCH, model.STN, rule=sequence_rule)

    pairs = [(i, k) for i in range(num_batches) for k in range(num_batches) if i < k]

    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.y = pyo.Var(model.PAIRS, model.STN, within=pyo.Binary)

    def disj_1_rule(mdl, i, k, j):
        return mdl.start[k, j] >= mdl.finish[i, j] - big_m * (1 - mdl.y[i, k, j])
    model.disj_1 = pyo.Constraint(model.PAIRS, model.STN, rule=disj_1_rule)

    def disj_2_rule(mdl, i, k, j):
        return mdl.start[i, j] >= mdl.finish[k, j] - big_m * mdl.y[i, k, j]
    model.disj_2 = pyo.Constraint(model.PAIRS, model.STN, rule=disj_2_rule)

    def makespan_rule(mdl, i):
        return mdl.makespan >= mdl.finish[i, num_stations - 1]
    model.makespan_con = pyo.Constraint(model.BATCH, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}