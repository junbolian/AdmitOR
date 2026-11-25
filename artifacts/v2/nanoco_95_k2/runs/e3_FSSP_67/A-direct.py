import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_time"]

    num_batches = len(pt)
    num_stations = len(pt[0])
    batches = range(num_batches)
    stations = range(num_stations)

    # Big-M chosen large enough to be non-binding
    total_time = sum(pt[b][s] for b in batches for s in stations)

    model = pyo.ConcreteModel()

    model.BATCH = pyo.Set(initialize=list(batches))
    model.STATION = pyo.Set(initialize=list(stations))
    model.PAIR = pyo.Set(
        initialize=[(i, j) for i in batches for j in batches if i < j],
        dimen=2,
    )

    # Start time of each batch on each station
    model.start = pyo.Var(model.BATCH, model.STATION, within=pyo.NonNegativeReals)
    # Makespan
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Binary ordering: y[i,j] = 1 if batch i precedes batch j on a given station
    model.y = pyo.Var(model.PAIR, model.STATION, within=pyo.Binary)

    def precedence_rule(m, b, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.start[b, s] >= m.start[b, s - 1] + pt[b][s - 1]

    model.precedence = pyo.Constraint(model.BATCH, model.STATION, rule=precedence_rule)

    def makespan_rule(m, b):
        return m.makespan >= m.start[b, num_stations - 1] + pt[b][num_stations - 1]

    model.makespan_con = pyo.Constraint(model.BATCH, rule=makespan_rule)

    def disj_rule(m, i, j, s):
        return m.start[i, s] + pt[i][s] <= m.start[j, s] + total_time * (1 - m.y[i, j, s])

    def disj_rule2(m, i, j, s):
        return m.start[j, s] + pt[j][s] <= m.start[i, s] + total_time * m.y[i, j, s]

    model.disj1 = pyo.Constraint(model.PAIR, model.STATION, rule=disj_rule)
    model.disj2 = pyo.Constraint(model.PAIR, model.STATION, rule=disj_rule2)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}