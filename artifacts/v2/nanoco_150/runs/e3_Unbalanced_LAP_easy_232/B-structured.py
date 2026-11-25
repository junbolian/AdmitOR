# IR: {"sets":{"technicians":"0..5","jobs":"0..5"},"params":{"cost_matrix":"input dispatch costs indexed by technician and job"},"variables":{"assignment[i,j]":"binary"},"constraints":["For each technician i: sum_j assignment[i,j] = 1","For each job j: sum_i assignment[i,j] = 1"],"objective":"Minimize sum_i sum_j cost_matrix[i][j] * assignment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.technicians = pyo.RangeSet(0, 5)
    model.jobs = pyo.RangeSet(0, 5)

    model.dispatch_cost = pyo.Param(
        model.technicians,
        model.jobs,
        initialize={
            (tech, job): cost_matrix[tech][job]
            for tech in model.technicians
            for job in model.jobs
        },
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.technicians,
        model.jobs,
        domain=pyo.Binary,
    )

    def technician_rule(mdl, tech):
        return sum(mdl.assignment[tech, job] for job in mdl.jobs) == 1

    model.technician_assignment = pyo.Constraint(
        model.technicians,
        rule=technician_rule,
    )

    def job_rule(mdl, job):
        return sum(
            mdl.assignment[tech, job] for tech in mdl.technicians
        ) == 1

    model.job_assignment = pyo.Constraint(model.jobs, rule=job_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.dispatch_cost[tech, job] * model.assignment[tech, job]
            for tech in model.technicians
            for job in model.jobs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}