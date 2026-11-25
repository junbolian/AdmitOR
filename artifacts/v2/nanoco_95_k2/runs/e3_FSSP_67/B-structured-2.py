# IR: {"sets":{"B":[0,1,2],"S":[0,1,2],"P":[[0,1],[0,2],[1,2]]},"params":{"processing_time":"nonnegative matrix read from params['processing_time']","H":"sum of all processing_time entries"},"variables":{"start[b,s]":"continuous [0,H]","finish[b,s]":"continuous [0,H]","before[i,j,s]":"binary for (i,j) in P","makespan":"continuous [0,H]"},"constraints":["finish[b,s] = start[b,s] + processing_time[b,s]","start[b,1] = finish[b,0] (immediate transfer)","start[b,2] >= finish[b,1]","start[j,s] >= finish[i,s] - H*(1-before[i,j,s])","start[i,s] >= finish[j,s] - H*before[i,j,s]","makespan >= finish[b,2]"],"objective":"minimize makespan"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]

    model = pyo.ConcreteModel()

    model.batches = pyo.Set(initialize=range(3), ordered=True)
    model.stations = pyo.Set(initialize=range(3), ordered=True)
    model.batch_pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (1, 2)],
    )

    model.duration = pyo.Param(
        model.batches,
        model.stations,
        initialize={
            (batch, station): processing_time[batch][station]
            for batch in model.batches
            for station in model.stations
        },
        within=pyo.NonNegativeReals,
    )

    horizon = sum(
        pyo.value(model.duration[batch, station])
        for batch in model.batches
        for station in model.stations
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

    def finish_rule(mdl, batch, station):
        return (
            mdl.finish[batch, station]
            == mdl.start[batch, station] + mdl.duration[batch, station]
        )

    model.operation_completion = pyo.Constraint(
        model.batches,
        model.stations,
        rule=finish_rule,
    )

    def immediate_transfer_rule(mdl, batch):
        return mdl.start[batch, 1] == mdl.finish[batch, 0]

    model.immediate_transfer = pyo.Constraint(
        model.batches,
        rule=immediate_transfer_rule,
    )

    def final_stage_rule(mdl, batch):
        return mdl.start[batch, 2] >= mdl.finish[batch, 1]

    model.final_stage_precedence = pyo.Constraint(
        model.batches,
        rule=final_stage_rule,
    )

    def forward_order_rule(mdl, first, second, station):
        return (
            mdl.start[second, station]
            >= mdl.finish[first, station]
            - horizon * (1 - mdl.before[first, second, station])
        )

    model.forward_station_order = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=forward_order_rule,
    )

    def reverse_order_rule(mdl, first, second, station):
        return (
            mdl.start[first, station]
            >= mdl.finish[second, station]
            - horizon * mdl.before[first, second, station]
        )

    model.reverse_station_order = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=reverse_order_rule,
    )

    def makespan_rule(mdl, batch):
        return mdl.makespan >= mdl.finish[batch, 2]

    model.makespan_bound = pyo.Constraint(
        model.batches,
        rule=makespan_rule,
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}