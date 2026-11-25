# IR: {"sets":{"strategies":[1,2,3,4,5,6,7,8],"segments":"1..39","coverage":{"1":[1,2,3,4,7],"2":[1,3,5,6,7,8],"3":[2,3,4,5,7],"4":[5,6],"5":[2,3,5,7,8],"6":[3,6,7,8],"7":[7],"8":[4,8],"9":[2,3,6,8],"10":[2,4,7],"11":[5,6],"12":[1,2,4,7],"13":[2,3,4,6,8],"14":[1,2,3,7],"15":[5,6],"16":[1,2,3,5,6,7,8],"17":[7],"18":[1,4,6],"19":[2,5,7],"20":[3,6],"21":[1,4,5,6],"22":[2,5,6,8],"23":[1,8],"24":[4,5,6,8],"25":[1],"26":[1,2,4,8],"27":[7],"28":[2,4],"29":[1,2,4,6],"30":[7,8],"31":[3,4],"32":[5,8],"33":[4,6],"34":[3,5,7],"35":[3,5,6],"36":[1,3,4,5],"37":[2],"38":[1,2,6],"39":[1,2,3,4,7,8]}},"params":{"cost_strategy_1":"real cost","cost_strategy_2":"real cost","cost_strategy_3":"real cost","cost_strategy_4":"real cost","cost_strategy_5":"real cost","cost_strategy_6":"real cost","cost_strategy_7":"real cost","cost_strategy_8":"real cost"},"decision_variables":{"selected[s]":"binary, s in strategies"},"constraints":["For each segment i: sum(selected[s] for s in coverage[i]) >= 1"],"objective":"minimize sum(cost_strategy_s * selected[s] for s in strategies)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["cost_strategy_1"],
        2: params["cost_strategy_2"],
        3: params["cost_strategy_3"],
        4: params["cost_strategy_4"],
        5: params["cost_strategy_5"],
        6: params["cost_strategy_6"],
        7: params["cost_strategy_7"],
        8: params["cost_strategy_8"],
    }

    coverage = {
        1: (1, 2, 3, 4, 7),
        2: (1, 3, 5, 6, 7, 8),
        3: (2, 3, 4, 5, 7),
        4: (5, 6),
        5: (2, 3, 5, 7, 8),
        6: (3, 6, 7, 8),
        7: (7,),
        8: (4, 8),
        9: (2, 3, 6, 8),
        10: (2, 4, 7),
        11: (5, 6),
        12: (1, 2, 4, 7),
        13: (2, 3, 4, 6, 8),
        14: (1, 2, 3, 7),
        15: (5, 6),
        16: (1, 2, 3, 5, 6, 7, 8),
        17: (7,),
        18: (1, 4, 6),
        19: (2, 5, 7),
        20: (3, 6),
        21: (1, 4, 5, 6),
        22: (2, 5, 6, 8),
        23: (1, 8),
        24: (4, 5, 6, 8),
        25: (1,),
        26: (1, 2, 4, 8),
        27: (7,),
        28: (2, 4),
        29: (1, 2, 4, 6),
        30: (7, 8),
        31: (3, 4),
        32: (5, 8),
        33: (4, 6),
        34: (3, 5, 7),
        35: (3, 5, 6),
        36: (1, 3, 4, 5),
        37: (2,),
        38: (1, 2, 6),
        39: (1, 2, 3, 4, 7, 8),
    }

    model = pyo.ConcreteModel()
    model.strategies = pyo.RangeSet(1, 8)
    model.segments = pyo.RangeSet(1, 39)
    model.strategy_cost = pyo.Param(
        model.strategies, initialize=costs, within=pyo.Reals
    )
    model.selected = pyo.Var(model.strategies, domain=pyo.Binary)

    def coverage_rule(instance, segment):
        return sum(
            instance.selected[strategy] for strategy in coverage[segment]
        ) >= 1

    model.segment_coverage = pyo.Constraint(
        model.segments, rule=coverage_rule
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
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        # Other runtime errors are unexpected and must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}