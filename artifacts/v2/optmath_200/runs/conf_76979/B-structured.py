# IR: {"sets":{"jobs":[0,1,2],"operations":[0,1],"machines":[0,1],"machine_pairs":"(j,k,o) for j<k and o in operations"},"params":{"processing_time_per_operation":"params['processing_time_per_operation']","big_M":"params['big_M']"},"assignment":"Assumption: operation o of every job uses machine o; the problem does not specify machine assignments.","variables":{"start[j,o]":"NonNegativeReals","order[j,k,o]":"Binary","makespan":"NonNegativeReals"},"constraints":["start[j,1] >= start[j,0] + processing_time_per_operation for each job j","start[k,o] >= start[j,o] + processing_time_per_operation - big_M*(1-order[j,k,o]) for each machine pair (j,k,o)","start[j,o] >= start[k,o] + processing_time_per_operation - big_M*order[j,k,o] for each machine pair (j,k,o)","makespan >= start[j,o] + processing_time_per_operation for every (j,o)"],"objective":"minimize makespan"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.operations = pyo.Set(initialize=[0, 1], ordered=True)
    model.machines = pyo.Set(initialize=[0, 1], ordered=True)

    model.processing_time = pyo.Param(
        initialize=params["processing_time_per_operation"]
    )
    model.sequencing_limit = pyo.Param(initialize=params["big_M"])

    # Each operation index denotes its assigned machine.
    model.machine_pairs = pyo.Set(
        dimen=3,
        initialize=[
            (first_job, second_job, operation)
            for first_job in model.jobs
            for second_job in model.jobs
            if first_job < second_job
            for operation in model.operations
        ],
    )

    model.start = pyo.Var(
        model.jobs, model.operations, domain=pyo.NonNegativeReals
    )
    model.order = pyo.Var(model.machine_pairs, domain=pyo.Binary)
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def precedence_rule(instance, job):
        return (
            instance.start[job, 1]
            >= instance.start[job, 0] + instance.processing_time
        )

    model.job_precedence = pyo.Constraint(
        model.jobs, rule=precedence_rule
    )

    def forward_sequence_rule(instance, first_job, second_job, operation):
        return (
            instance.start[second_job, operation]
            >= instance.start[first_job, operation]
            + instance.processing_time
            - instance.sequencing_limit
            * (1 - instance.order[first_job, second_job, operation])
        )

    model.forward_sequence = pyo.Constraint(
        model.machine_pairs, rule=forward_sequence_rule
    )

    def reverse_sequence_rule(instance, first_job, second_job, operation):
        return (
            instance.start[first_job, operation]
            >= instance.start[second_job, operation]
            + instance.processing_time
            - instance.sequencing_limit
            * instance.order[first_job, second_job, operation]
        )

    model.reverse_sequence = pyo.Constraint(
        model.machine_pairs, rule=reverse_sequence_rule
    )

    def completion_bound_rule(instance, job, operation):
        return (
            instance.makespan
            >= instance.start[job, operation] + instance.processing_time
        )

    model.completion_bounds = pyo.Constraint(
        model.jobs, model.operations, rule=completion_bound_rule
    )

    model.makespan_objective = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}