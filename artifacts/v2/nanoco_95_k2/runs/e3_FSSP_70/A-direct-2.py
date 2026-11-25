import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]
    num_jobs = int(params["num_jobs"])
    num_stations = int(params["num_stations"])

    model = pyo.ConcreteModel()

    jobs = list(range(num_jobs))
    stations = list(range(num_stations))

    model.J = pyo.Set(initialize=jobs)
    model.S = pyo.Set(initialize=stations)
    model.JS = pyo.Set(initialize=[(j, s) for j in jobs for s in stations], dimen=2)

    model.p = pyo.Param(
        model.JS,
        initialize={(j, s): processing_times[j][s] for j in jobs for s in stations},
    )

    bigM = sum(processing_times[j][s] for j in jobs for s in stations)

    model.start = pyo.Var(model.JS, within=pyo.NonNegativeReals)
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)

    # Precedence: job flows through stations in order
    model.precedence = pyo.ConstraintList()
    for j in jobs:
        for s in stations:
            if s >= 1:
                model.precedence.add(
                    model.start[j, s] >= model.start[j, s - 1] + model.p[j, s - 1]
                )

    # Disjunctive: no two jobs overlap on the same station
    model.y = pyo.Var(model.S, model.J, model.J, within=pyo.Binary)
    model.disj = pyo.ConstraintList()
    for s in stations:
        for j1 in jobs:
            for j2 in jobs:
                if j1 < j2:
                    model.disj.add(
                        model.start[j1, s] + model.p[j1, s]
                        <= model.start[j2, s] + bigM * (1 - model.y[s, j1, j2])
                    )
                    model.disj.add(
                        model.start[j2, s] + model.p[j2, s]
                        <= model.start[j1, s] + bigM * model.y[s, j1, j2]
                    )

    # Makespan
    model.makespan = pyo.ConstraintList()
    for j in jobs:
        model.makespan.add(
            model.Cmax >= model.start[j, stations[-1]] + model.p[j, stations[-1]]
        )

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}