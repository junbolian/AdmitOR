# IR: {"sets":{"J":[0,1,2],"U":[0,1,2],"O":"J x U","A":[[0,1,0],[0,0,2],[1,1,2],[1,2,0],[2,1,0],[2,0,2]],"P":"{(u,a,b): u in U, a,b in J, a<b}"},"params":{"duration[0,1]":"cycle_time_J0_M1","duration[0,0]":"cycle_time_J0_M0","duration[0,2]":"cycle_time_J0_M2","duration[1,1]":"cycle_time_J1_M1","duration[1,2]":"cycle_time_J1_M2","duration[1,0]":"cycle_time_J1_M0","duration[2,1]":"cycle_time_J2_M1","duration[2,0]":"cycle_time_J2_M0","duration[2,2]":"cycle_time_J2_M2","duration_domain":"nonnegative real","H":"sum(duration[j,u] for (j,u) in O)"},"variables":{"start[j,u]":"continuous, 0 <= start[j,u] <= H-duration[j,u]","before[u,a,b]":"binary; 1 means batch a precedes batch b on unit u","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[j,v] >= start[j,u]+duration[j,u] for (j,u,v) in A","start[a,u]+duration[a,u] <= start[b,u]+H*(1-before[u,a,b]) for (u,a,b) in P","start[b,u]+duration[b,u] <= start[a,u]+H*before[u,a,b] for (u,a,b) in P","makespan >= start[j,u]+duration[j,u] for (j,u) in O"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.J = pyo.Set(initialize=range(3), ordered=True)
    model.U = pyo.Set(initialize=range(3), ordered=True)
    model.O = pyo.Set(
        dimen=2,
        initialize=[(job, unit) for job in range(3) for unit in range(3)],
    )
    model.A = pyo.Set(
        dimen=3,
        initialize=[
            (0, 1, 0),
            (0, 0, 2),
            (1, 1, 2),
            (1, 2, 0),
            (2, 1, 0),
            (2, 0, 2),
        ],
    )
    model.P = pyo.Set(
        dimen=3,
        initialize=[
            (unit, first, second)
            for unit in range(3)
            for first in range(3)
            for second in range(first + 1, 3)
        ],
    )

    model.duration = pyo.Param(
        model.O,
        within=pyo.NonNegativeReals,
        initialize={
            (0, 1): params["cycle_time_J0_M1"],
            (0, 0): params["cycle_time_J0_M0"],
            (0, 2): params["cycle_time_J0_M2"],
            (1, 1): params["cycle_time_J1_M1"],
            (1, 2): params["cycle_time_J1_M2"],
            (1, 0): params["cycle_time_J1_M0"],
            (2, 1): params["cycle_time_J2_M1"],
            (2, 0): params["cycle_time_J2_M0"],
            (2, 2): params["cycle_time_J2_M2"],
        },
    )
    model.H = pyo.Param(
        initialize=sum(
            pyo.value(model.duration[job, unit])
            for job, unit in model.O
        ),
        within=pyo.NonNegativeReals,
    )

    def start_bounds(instance, job, unit):
        return (0, instance.H - instance.duration[job, unit])

    model.start = pyo.Var(
        model.O,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.P, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, pyo.value(model.H)),
    )

    def precedence_rule(instance, job, previous_unit, next_unit):
        return (
            instance.start[job, next_unit]
            >= instance.start[job, previous_unit]
            + instance.duration[job, previous_unit]
        )

    model.precedence = pyo.Constraint(model.A, rule=precedence_rule)

    def first_before_second_rule(instance, unit, first, second):
        return (
            instance.start[first, unit] + instance.duration[first, unit]
            <= instance.start[second, unit]
            + instance.H * (1 - instance.before[unit, first, second])
        )

    model.first_before_second = pyo.Constraint(
        model.P, rule=first_before_second_rule
    )

    def second_before_first_rule(instance, unit, first, second):
        return (
            instance.start[second, unit] + instance.duration[second, unit]
            <= instance.start[first, unit]
            + instance.H * instance.before[unit, first, second]
        )

    model.second_before_first = pyo.Constraint(
        model.P, rule=second_before_first_rule
    )

    def completion_rule(instance, job, unit):
        return (
            instance.makespan
            >= instance.start[job, unit] + instance.duration[job, unit]
        )

    model.completion = pyo.Constraint(model.O, rule=completion_rule)
    model.objective = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}