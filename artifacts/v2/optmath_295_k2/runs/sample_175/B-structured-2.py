# IR (JSON):
# {
#   "sets": {
#     "strategies": [1, 2, 3, 4, 5, 6, 7, 8],
#     "segments": {"start": 1, "stop_inclusive": 39},
#     "coverage_by_segment": [
#       [1, 2, 3, 4, 7], [1, 3, 5, 6, 7, 8], [2, 3, 4, 5, 7],
#       [5, 6], [2, 3, 5, 7, 8], [3, 6, 7, 8], [7], [4, 8],
#       [2, 3, 6, 8], [2, 4, 7], [5, 6], [1, 2, 4, 7],
#       [2, 3, 4, 6, 8], [1, 2, 3, 7], [5, 6],
#       [1, 2, 3, 5, 6, 7, 8], [7], [1, 4, 6], [2, 5, 7],
#       [3, 6], [1, 4, 5, 6], [2, 5, 6, 8], [1, 8],
#       [4, 5, 6, 8], [1], [1, 2, 4, 8], [7], [2, 4],
#       [1, 2, 4, 6], [7, 8], [3, 4], [5, 8], [4, 6],
#       [3, 5, 7], [3, 5, 6], [1, 3, 4, 5], [2],
#       [1, 2, 6], [1, 2, 3, 4, 7, 8]
#     ]
#   },
#   "params": {
#     "strategy_costs": "params['strategy_costs']; eight-element sequence in strategy order, or mapping with strategy IDs as integer or string keys"
#   },
#   "decision_variables": {
#     "selected[strategy]": {"type": "binary", "index": "strategies"}
#   },
#   "constraints": [
#     "For each segment: sum(selected[strategy] for strategy in coverage_by_segment[segment]) >= 1"
#   ],
#   "objective": {
#     "sense": "minimize",
#     "expression": "sum(strategy_costs[strategy] * selected[strategy] for strategy in strategies)"
#   }
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_costs = params["strategy_costs"]
    strategies = range(1, 9)

    if isinstance(raw_costs, Mapping):
        costs = {
            strategy: (
                raw_costs[strategy]
                if strategy in raw_costs
                else raw_costs[str(strategy)]
            )
            for strategy in strategies
        }
    else:
        costs = {
            strategy: raw_costs[strategy - 1]
            for strategy in strategies
        }

    coverage = (
        (1, 2, 3, 4, 7),          # Segment 1
        (1, 3, 5, 6, 7, 8),       # Segment 2
        (2, 3, 4, 5, 7),          # Segment 3
        (5, 6),                   # Segment 4
        (2, 3, 5, 7, 8),          # Segment 5
        (3, 6, 7, 8),             # Segment 6
        (7,),                     # Segment 7
        (4, 8),                   # Segment 8
        (2, 3, 6, 8),             # Segment 9
        (2, 4, 7),                # Segment 10
        (5, 6),                   # Segment 11
        (1, 2, 4, 7),             # Segment 12
        (2, 3, 4, 6, 8),          # Segment 13
        (1, 2, 3, 7),             # Segment 14
        (5, 6),                   # Segment 15
        (1, 2, 3, 5, 6, 7, 8),    # Segment 16
        (7,),                     # Segment 17
        (1, 4, 6),                # Segment 18
        (2, 5, 7),                # Segment 19
        (3, 6),                   # Segment 20
        (1, 4, 5, 6),             # Segment 21
        (2, 5, 6, 8),             # Segment 22
        (1, 8),                   # Segment 23
        (4, 5, 6, 8),             # Segment 24
        (1,),                     # Segment 25
        (1, 2, 4, 8),             # Segment 26
        (7,),                     # Segment 27
        (2, 4),                   # Segment 28
        (1, 2, 4, 6),             # Segment 29
        (7, 8),                   # Segment 30
        (3, 4),                   # Segment 31
        (5, 8),                   # Segment 32
        (4, 6),                   # Segment 33
        (3, 5, 7),                # Segment 34
        (3, 5, 6),                # Segment 35
        (1, 3, 4, 5),             # Segment 36
        (2,),                     # Segment 37
        (1, 2, 6),                # Segment 38
        (1, 2, 3, 4, 7, 8),       # Segment 39
    )

    model = pyo.ConcreteModel()
    model.strategies = pyo.RangeSet(1, 8)
    model.segments = pyo.RangeSet(1, 39)
    model.strategy_costs = pyo.Param(
        model.strategies,
        initialize=costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.strategies, domain=pyo.Binary)

    def coverage_rule(instance, segment):
        return sum(
            instance.selected[strategy]
            for strategy in coverage[segment - 1]
        ) >= 1

    model.segment_coverage = pyo.Constraint(
        model.segments,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.strategy_costs[strategy] * model.selected[strategy]
            for strategy in model.strategies
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}