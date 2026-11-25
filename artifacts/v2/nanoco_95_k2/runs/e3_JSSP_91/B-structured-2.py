# IR: {"sets":{"lots":[0,1,2],"tools":[0,1,2],"route_arcs":[[1,0],[0,2]],"lot_pairs":[[0,1],[0,2],[1,2]]},"params":{"p_0_1":"processing time","p_0_0":"processing time","p_0_2":"processing time","p_1_1":"processing time","p_1_0":"processing time","p_1_2":"processing time","p_2_1":"processing time","p_2_0":"processing time","p_2_2":"processing time"},"derived":{"p[i,t]":"params['p_'+str(i)+'_'+str(t)]","H":"sum(p[i,t] for all lots i and tools t)"},"variables":{"start[i,t]":"continuous, 0 <= start[i,t] <= H-p[i,t]","before[i,j,t]":"binary for i<j; 1 means i precedes j on tool t","makespan":"continuous, 0 <= makespan <= H"},"constraints":["start[i,u]+p[i,u] <= start[i,v] for each lot i and route arc (u,v)","start[i,t]+p[i,t] <= start[j,t]+H*(1-before[i,j,t]) for each lot pair (i,j) and tool t","start[j,t]+p[j,t] <= start[i,t]+H*before[i,j,t] for each lot pair (i,j) and tool t","makespan >= start[i,2]+p[i,2] for each lot i"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.lots = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.tools = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.route_arcs = pyo.Set(
        dimen=2, initialize=[(1, 0), (0, 2)], ordered=True
    )
    model.lot_pairs = pyo.Set(
        dimen=2, initialize=[(0, 1), (0, 2), (1, 2)], ordered=True
    )

    processing = {
        (lot, tool): params[f"p_{lot}_{tool}"]
        for lot in model.lots
        for tool in model.tools
    }
    horizon = sum(processing.values())

    model.processing = pyo.Param(
        model.lots,
        model.tools,
        initialize=processing,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon, within=pyo.NonNegativeReals
    )

    def start_bounds(block, lot, tool):
        return (
            0,
            pyo.value(block.horizon - block.processing[lot, tool]),
        )

    model.start = pyo.Var(
        model.lots,
        model.tools,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(
        model.lot_pairs, model.tools, domain=pyo.Binary
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, horizon)
    )

    def route_rule(block, lot, first_tool, next_tool):
        return (
            block.start[lot, first_tool]
            + block.processing[lot, first_tool]
            <= block.start[lot, next_tool]
        )

    model.route_precedence = pyo.Constraint(
        model.lots, model.route_arcs, rule=route_rule
    )

    def forward_rule(block, first_lot, second_lot, tool):
        return (
            block.start[first_lot, tool]
            + block.processing[first_lot, tool]
            <= block.start[second_lot, tool]
            + block.horizon * (1 - block.before[first_lot, second_lot, tool])
        )

    model.tool_forward = pyo.Constraint(
        model.lot_pairs, model.tools, rule=forward_rule
    )

    def reverse_rule(block, first_lot, second_lot, tool):
        return (
            block.start[second_lot, tool]
            + block.processing[second_lot, tool]
            <= block.start[first_lot, tool]
            + block.horizon * block.before[first_lot, second_lot, tool]
        )

    model.tool_reverse = pyo.Constraint(
        model.lot_pairs, model.tools, rule=reverse_rule
    )

    def completion_rule(block, lot):
        return (
            block.makespan
            >= block.start[lot, 2] + block.processing[lot, 2]
        )

    model.completion_bound = pyo.Constraint(
        model.lots, rule=completion_rule
    )
    model.total_makespan = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}