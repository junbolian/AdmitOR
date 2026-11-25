# IR: {"sets":{"lots":[0,1,2],"tools":[0,1,2],"route_arcs":[[1,0],[0,2]],"lot_pairs":[[0,1],[0,2],[1,2]]},"params":{"p[lot,tool]":"params['p_<lot>_<tool>'], nonnegative","H":"sum(p[lot,tool] for all lots and tools)"},"variables":{"start[lot,tool]":"continuous in [0,H]","before[first,second,tool]":"binary for first<second","makespan":"continuous in [0,H]"},"constraints":["start[lot,next]>=start[lot,previous]+p[lot,previous] for each route arc","start[first,tool]+p[first,tool]<=start[second,tool]+H*(1-before[first,second,tool])","start[second,tool]+p[second,tool]<=start[first,tool]+H*before[first,second,tool]","makespan>=start[lot,2]+p[lot,2] for each lot"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        (0, 1): params["p_0_1"],
        (0, 0): params["p_0_0"],
        (0, 2): params["p_0_2"],
        (1, 1): params["p_1_1"],
        (1, 0): params["p_1_0"],
        (1, 2): params["p_1_2"],
        (2, 1): params["p_2_1"],
        (2, 0): params["p_2_0"],
        (2, 2): params["p_2_2"],
    }
    horizon = sum(processing_times.values())

    model = pyo.ConcreteModel()
    model.lots = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.tools = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.route_arcs = pyo.Set(
        dimen=2, initialize=[(1, 0), (0, 2)], ordered=True
    )
    model.lot_pairs = pyo.Set(
        dimen=2, initialize=[(0, 1), (0, 2), (1, 2)], ordered=True
    )

    model.processing_time = pyo.Param(
        model.lots,
        model.tools,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.lots,
        model.tools,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.lot_pairs,
        model.tools,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def route_rule(block, lot, previous_tool, next_tool):
        return (
            block.start[lot, next_tool]
            >= block.start[lot, previous_tool]
            + block.processing_time[lot, previous_tool]
        )

    model.route_precedence = pyo.Constraint(
        model.lots, model.route_arcs, rule=route_rule
    )

    def first_before_second_rule(block, first, second, tool):
        return (
            block.start[first, tool] + block.processing_time[first, tool]
            <= block.start[second, tool]
            + block.horizon * (1 - block.before[first, second, tool])
        )

    model.tool_order_forward = pyo.Constraint(
        model.lot_pairs, model.tools, rule=first_before_second_rule
    )

    def second_before_first_rule(block, first, second, tool):
        return (
            block.start[second, tool] + block.processing_time[second, tool]
            <= block.start[first, tool]
            + block.horizon * block.before[first, second, tool]
        )

    model.tool_order_reverse = pyo.Constraint(
        model.lot_pairs, model.tools, rule=second_before_first_rule
    )

    def completion_rule(block, lot):
        return (
            block.makespan
            >= block.start[lot, 2] + block.processing_time[lot, 2]
        )

    model.completion_bound = pyo.Constraint(
        model.lots, rule=completion_rule
    )
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