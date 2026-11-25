# IR: {"sets":{"batches":[0,1,2],"stages":[1,2,3],"operations":"batches x stages","unit_route":{"0":[1,0,2],"1":[1,0,2],"2":[2,1,0]},"conflict_pairs":"unordered pairs of operations assigned to the same unit"},"params":["processing_time_B0_on_U1_stage1","processing_time_B0_on_U0_stage2","processing_time_B0_on_U2_stage3","processing_time_B1_on_U1_stage1","processing_time_B1_on_U0_stage2","processing_time_B1_on_U2_stage3","processing_time_B2_on_U2_stage1","processing_time_B2_on_U1_stage2","processing_time_B2_on_U0_stage3"],"derived":{"duration":"parameter matching each operation","H":"sum of all operation durations"},"variables":{"start[batch,stage]":"continuous in [0,H]","makespan":"continuous in [0,H]","before[conflict_pair]":"binary; 1 means first operation precedes second"},"constraints":["start[b,s+1] >= start[b,s] + duration[b,s] for s=1,2","start[first] + duration[first] <= start[second] + H*(1-before[pair]) for each conflict_pair","start[second] + duration[second] <= start[first] + H*before[pair] for each conflict_pair","makespan >= start[b,s] + duration[b,s] for every operation"],"objective":"minimize makespan"}
# Routing assumption: the explicit PARAMS unit/stage assignments govern.
# Batch 0 therefore follows U1 -> U0 -> U2; its narrative route conflicts.

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = {
        (0, 1): params["processing_time_B0_on_U1_stage1"],
        (0, 2): params["processing_time_B0_on_U0_stage2"],
        (0, 3): params["processing_time_B0_on_U2_stage3"],
        (1, 1): params["processing_time_B1_on_U1_stage1"],
        (1, 2): params["processing_time_B1_on_U0_stage2"],
        (1, 3): params["processing_time_B1_on_U2_stage3"],
        (2, 1): params["processing_time_B2_on_U2_stage1"],
        (2, 2): params["processing_time_B2_on_U1_stage2"],
        (2, 3): params["processing_time_B2_on_U0_stage3"],
    }

    routes = {
        0: (1, 0, 2),
        1: (1, 0, 2),
        2: (2, 1, 0),
    }
    operations = [
        (batch, stage)
        for batch in range(3)
        for stage in range(1, 4)
    ]
    assigned_unit = {
        (batch, stage): routes[batch][stage - 1]
        for batch, stage in operations
    }
    conflict_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
        if assigned_unit[first] == assigned_unit[second]
    ]

    model = pyo.ConcreteModel()
    model.batches = pyo.Set(initialize=range(3), ordered=True)
    model.stages = pyo.Set(initialize=range(1, 4), ordered=True)
    model.operations = pyo.Set(
        dimen=2, initialize=operations, ordered=True
    )
    model.conflict_pairs = pyo.Set(
        dimen=4, initialize=conflict_pairs, ordered=True
    )

    model.duration = pyo.Param(
        model.operations,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    horizon = sum(
        pyo.value(model.duration[batch, stage])
        for batch, stage in operations
    )
    model.horizon = pyo.Param(
        initialize=horizon, within=pyo.NonNegativeReals
    )

    # A fully serial schedule is feasible within this horizon.
    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.conflict_pairs, domain=pyo.Binary
    )

    def precedence_rule(instance, batch, stage):
        return (
            instance.start[batch, stage + 1]
            >= instance.start[batch, stage]
            + instance.duration[batch, stage]
        )

    model.stage_precedence = pyo.Constraint(
        model.batches, (1, 2), rule=precedence_rule
    )

    def first_before_second_rule(
        instance, first_batch, first_stage, second_batch, second_stage
    ):
        return (
            instance.start[first_batch, first_stage]
            + instance.duration[first_batch, first_stage]
            <= instance.start[second_batch, second_stage]
            + instance.horizon
            * (
                1
                - instance.before[
                    first_batch, first_stage, second_batch, second_stage
                ]
            )
        )

    model.unit_order_forward = pyo.Constraint(
        model.conflict_pairs, rule=first_before_second_rule
    )

    def second_before_first_rule(
        instance, first_batch, first_stage, second_batch, second_stage
    ):
        return (
            instance.start[second_batch, second_stage]
            + instance.duration[second_batch, second_stage]
            <= instance.start[first_batch, first_stage]
            + instance.horizon
            * instance.before[
                first_batch, first_stage, second_batch, second_stage
            ]
        )

    model.unit_order_reverse = pyo.Constraint(
        model.conflict_pairs, rule=second_before_first_rule
    )

    def completion_rule(instance, batch, stage):
        return (
            instance.makespan
            >= instance.start[batch, stage]
            + instance.duration[batch, stage]
        )

    model.completion_bound = pyo.Constraint(
        model.operations, rule=completion_rule
    )
    model.total_cycle_time = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}