# IR: {"sets":{"J":[0,1,2],"K":[0,1,2],"O":"J x K","routes":[[2,0,1],[0,2,1],[0,2,1]],"P":"unordered pairs of distinct operations assigned to the same station"},"params":{"p[j,k]":"params['processing_times'][j][k]","H":"sum(p[j,k] for (j,k) in O)"},"variables":{"start[j,k]":"continuous, 0 <= start[j,k] <= H-p[j,k]","before[a,b]":"binary for each (a,b) in P","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[j,k+1] >= start[j,k]+p[j,k] for j in J, k in {0,1}","start[b] >= start[a]+p[a]-H*(1-before[a,b]) for (a,b) in P","start[a] >= start[b]+p[b]-H*before[a,b] for (a,b) in P","makespan >= start[j,2]+p[j,2] for j in J"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    jobs = range(3)
    steps = range(3)
    routes = (
        (2, 0, 1),
        (0, 2, 1),
        (0, 2, 1),
    )

    operations = [(job, step) for job in jobs for step in steps]
    durations = {
        (job, step): float(processing_times[job][step])
        for job, step in operations
    }
    horizon = sum(durations.values())

    station_pairs = [
        (job_a, step_a, job_b, step_b)
        for position, (job_a, step_a) in enumerate(operations)
        for job_b, step_b in operations[position + 1:]
        if routes[job_a][step_a] == routes[job_b][step_b]
    ]

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.operations = pyo.Set(dimen=2, initialize=operations, ordered=True)
    model.station_pairs = pyo.Set(
        dimen=4, initialize=station_pairs, ordered=True
    )
    model.precedence_arcs = pyo.Set(
        dimen=2,
        initialize=[(job, step) for job in jobs for step in range(2)],
        ordered=True,
    )

    model.duration = pyo.Param(
        model.operations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    def start_bounds(instance, job, step):
        return (
            0,
            pyo.value(instance.horizon - instance.duration[job, step]),
        )

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.station_pairs, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def precedence_rule(instance, job, step):
        return (
            instance.start[job, step + 1]
            >= instance.start[job, step] + instance.duration[job, step]
        )

    model.route_precedence = pyo.Constraint(
        model.precedence_arcs,
        rule=precedence_rule,
    )

    def station_forward_rule(instance, job_a, step_a, job_b, step_b):
        return (
            instance.start[job_b, step_b]
            >= instance.start[job_a, step_a]
            + instance.duration[job_a, step_a]
            - instance.horizon
            * (1 - instance.before[job_a, step_a, job_b, step_b])
        )

    model.station_forward = pyo.Constraint(
        model.station_pairs,
        rule=station_forward_rule,
    )

    def station_reverse_rule(instance, job_a, step_a, job_b, step_b):
        return (
            instance.start[job_a, step_a]
            >= instance.start[job_b, step_b]
            + instance.duration[job_b, step_b]
            - instance.horizon
            * instance.before[job_a, step_a, job_b, step_b]
        )

    model.station_reverse = pyo.Constraint(
        model.station_pairs,
        rule=station_reverse_rule,
    )

    def completion_rule(instance, job):
        return (
            instance.makespan
            >= instance.start[job, 2] + instance.duration[job, 2]
        )

    model.batch_completion = pyo.Constraint(
        model.jobs,
        rule=completion_rule,
    )

    model.total_lead_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_lead_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}