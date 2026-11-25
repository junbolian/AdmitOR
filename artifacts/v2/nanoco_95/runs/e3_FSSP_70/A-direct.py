import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    n_jobs = len(processing_times)
    n_stations = len(processing_times[0])
    jobs = range(n_jobs)
    stations = range(n_stations)

    model = pyo.ConcreteModel()

    model.J = pyo.Set(initialize=list(jobs))
    model.S = pyo.Set(initialize=list(stations))

    # Start times for each job on each station
    model.start = pyo.Var(model.J, model.S, within=pyo.NonNegativeReals)

    # Makespan
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)

    # Precedence constraints: operation on station s+1 must start after completion on s
    def precedence_rule(mdl, j, s):
        if s == 0:
            return pyo.Constraint.Skip
        return mdl.start[j, s] >= mdl.start[j, s - 1] + processing_times[j][s - 1]

    model.precedence = pyo.Constraint(model.J, model.S, rule=precedence_rule)

    # Makespan constraints
    def cmax_rule(mdl, j):
        return mdl.Cmax >= mdl.start[j, n_stations - 1] + processing_times[j][n_stations - 1]

    model.cmax_con = pyo.Constraint(model.J, rule=cmax_rule)

    # Disjunctive constraints for machine sequencing (at most one job per station at a time)
    model.pair = pyo.Set(
        initialize=[(i, k) for i in jobs for k in jobs if i < k],
        dimen=2,
    )
    model.binary = pyo.Var(model.pair, model.S, within=pyo.Binary)

    def mbig(i, k, s):
        return (
            processing_times[i][s]
            + processing_times[k][s]
            + sum(
                processing_times[i][s2] + processing_times[k][s2]
                for s2 in stations
            )
        )

    def disjunctive_ik(mdl, i, k, s):
        # binary = 1 means i before k; 0 means k before i
        return (
            mdl.start[i, s] + processing_times[i][s]
            <= mdl.start[k, s] + mbig(i, k, s) * (1 - mdl.binary[i, k, s])
        )

    def disjunctive_ki(mdl, i, k, s):
        return (
            mdl.start[k, s] + processing_times[k][s]
            <= mdl.start[i, s] + mbig(i, k, s) * mdl.binary[i, k, s]
        )

    model.seq_ik = pyo.Constraint(model.pair, model.S, rule=disjunctive_ik)
    model.seq_ki = pyo.Constraint(model.pair, model.S, rule=disjunctive_ki)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}