# IR:
# {
#   "sets": {"B": [0, 1, 2], "S": [0, 1, 2], "P": [[0, 1], [0, 2], [1, 2]]},
#   "params": ["pt_0_0", "pt_0_1", "pt_0_2", "pt_1_0", "pt_1_1", "pt_1_2", "pt_2_0", "pt_2_1", "pt_2_2"],
#   "derived": {"p[b,s]": "params['pt_' + str(b) + '_' + str(s)] >= 0", "H": "sum(p[b,s] for b in B for s in S)"},
#   "variables": {"start[b,s]": "continuous, [0,H]", "finish[b,s]": "continuous, [0,H]", "before[i,j,s]": "binary, (i,j) in P", "makespan": "continuous, [0,H]"},
#   "constraints": [
#     "finish[b,s] = start[b,s] + p[b,s] for b in B, s in S",
#     "start[b,1] = finish[b,0] for b in B (immediate transfer)",
#     "start[b,2] >= finish[b,1] for b in B",
#     "start[j,s] >= finish[i,s] - H*(1-before[i,j,s]) for (i,j) in P, s in S",
#     "start[i,s] >= finish[j,s] - H*before[i,j,s] for (i,j) in P, s in S",
#     "makespan >= finish[b,2] for b in B"
#   ],
#   "objective": "minimize makespan"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        (0, 0): params["pt_0_0"],
        (0, 1): params["pt_0_1"],
        (0, 2): params["pt_0_2"],
        (1, 0): params["pt_1_0"],
        (1, 1): params["pt_1_1"],
        (1, 2): params["pt_1_2"],
        (2, 0): params["pt_2_0"],
        (2, 1): params["pt_2_1"],
        (2, 2): params["pt_2_2"],
    }

    model = pyo.ConcreteModel()
    model.batches = pyo.RangeSet(0, 2)
    model.stations = pyo.RangeSet(0, 2)
    model.batch_pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (1, 2)],
    )

    model.processing_time = pyo.Param(
        model.batches,
        model.stations,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    # Processing whole batches consecutively provides a feasible horizon,
    # including the immediate transfer from Station 0 to Station 1.
    horizon = sum(
        pyo.value(model.processing_time[batch, station])
        for batch in model.batches
        for station in model.stations
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.batches,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.finish = pyo.Var(
        model.batches,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.batch_pairs,
        model.stations,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def duration_rule(instance, batch, station):
        return (
            instance.finish[batch, station]
            == instance.start[batch, station]
            + instance.processing_time[batch, station]
        )

    model.duration_constraints = pyo.Constraint(
        model.batches,
        model.stations,
        rule=duration_rule,
    )

    def immediate_transfer_rule(instance, batch):
        return instance.start[batch, 1] == instance.finish[batch, 0]

    model.immediate_transfer_constraints = pyo.Constraint(
        model.batches,
        rule=immediate_transfer_rule,
    )

    def final_station_precedence_rule(instance, batch):
        return instance.start[batch, 2] >= instance.finish[batch, 1]

    model.final_station_precedence_constraints = pyo.Constraint(
        model.batches,
        rule=final_station_precedence_rule,
    )

    def forward_capacity_rule(instance, first, second, station):
        return (
            instance.start[second, station]
            >= instance.finish[first, station]
            - instance.horizon * (1 - instance.before[first, second, station])
        )

    model.forward_capacity_constraints = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=forward_capacity_rule,
    )

    def reverse_capacity_rule(instance, first, second, station):
        return (
            instance.start[first, station]
            >= instance.finish[second, station]
            - instance.horizon * instance.before[first, second, station]
        )

    model.reverse_capacity_constraints = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=reverse_capacity_rule,
    )

    def makespan_rule(instance, batch):
        return instance.makespan >= instance.finish[batch, 2]

    model.makespan_constraints = pyo.Constraint(
        model.batches,
        rule=makespan_rule,
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this error when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}