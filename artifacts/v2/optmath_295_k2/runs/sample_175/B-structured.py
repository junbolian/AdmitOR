# IR: {"sets":{"strategies":"1..8","segments":"1..39","coverage":[[1,2,3,4,7],[1,3,5,6,7,8],[2,3,4,5,7],[5,6],[2,3,5,7,8],[3,6,7,8],[7],[4,8],[2,3,6,8],[2,4,7],[5,6],[1,2,4,7],[2,3,4,6,8],[1,2,3,7],[5,6],[1,2,3,5,6,7,8],[7],[1,4,6],[2,5,7],[3,6],[1,4,5,6],[2,5,6,8],[1,8],[4,5,6,8],[1],[1,2,4,8],[7],[2,4],[1,2,4,6],[7,8],[3,4],[5,8],[4,6],[3,5,7],[3,5,6],[1,3,4,5],[2],[1,2,6],[1,2,3,4,7,8]]},"params":{"strategy_costs":"params['strategy_costs']; ordered sequence for strategies 1..8 or mapping keyed by strategy number"},"decision_variables":{"selected[s]":"Binary for each strategy s"},"constraints":["For each segment t: sum(selected[s] for s in coverage[t]) >= 1"],"objective":"Minimize sum(strategy_costs[s] * selected[s] for s in strategies)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the minimum-cost promotional-strategy set-cover problem."""
    strategy_costs = params["strategy_costs"]

    coverage_rows = (
        (1, 2, 3, 4, 7),
        (1, 3, 5, 6, 7, 8),
        (2, 3, 4, 5, 7),
        (5, 6),
        (2, 3, 5, 7, 8),
        (3, 6, 7, 8),
        (7,),
        (4, 8),
        (2, 3, 6, 8),
        (2, 4, 7),
        (5, 6),
        (1, 2, 4, 7),
        (2, 3, 4, 6, 8),
        (1, 2, 3, 7),
        (5, 6),
        (1, 2, 3, 5, 6, 7, 8),
        (7,),
        (1, 4, 6),
        (2, 5, 7),
        (3, 6),
        (1, 4, 5, 6),
        (2, 5, 6, 8),
        (1, 8),
        (4, 5, 6, 8),
        (1,),
        (1, 2, 4, 8),
        (7,),
        (2, 4),
        (1, 2, 4, 6),
        (7, 8),
        (3, 4),
        (5, 8),
        (4, 6),
        (3, 5, 7),
        (3, 5, 6),
        (1, 3, 4, 5),
        (2,),
        (1, 2, 6),
        (1, 2, 3, 4, 7, 8),
    )

    if isinstance(strategy_costs, Mapping):
        cost_data = {
            strategy: strategy_costs[
                strategy if strategy in strategy_costs else str(strategy)
            ]
            for strategy in range(1, 9)
        }
    else:
        cost_data = {
            strategy: strategy_costs[strategy - 1]
            for strategy in range(1, 9)
        }

    model = pyo.ConcreteModel()
    model.strategies = pyo.RangeSet(1, 8)
    model.segments = pyo.RangeSet(1, 39)

    model.coverage = pyo.Set(
        model.segments,
        within=model.strategies,
        initialize={
            segment: coverage_rows[segment - 1]
            for segment in range(1, 40)
        },
    )
    model.strategy_cost = pyo.Param(
        model.strategies,
        initialize=cost_data,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.strategies, domain=pyo.Binary)

    def coverage_rule(instance, segment):
        return sum(
            instance.selected[strategy]
            for strategy in instance.coverage[segment]
        ) >= 1

    model.segment_coverage = pyo.Constraint(
        model.segments,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.strategy_cost[strategy] * model.selected[strategy]
            for strategy in model.strategies
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}