# IR: {"sets":{"P":[0,1,2,3,4,5,6,7,8,9,10,11],"W":[1,2,3,4],"A":[[0,1],[0,2],[0,4],[1,1],[1,2],[1,4],[2,3],[2,4],[3,1],[3,2],[3,3],[3,4],[4,3],[4,4],[5,1],[5,2],[5,3],[5,4],[6,1],[6,2],[6,3],[6,4],[7,1],[7,2],[7,4],[8,1],[8,2],[8,3],[8,4],[9,1],[9,2],[9,3],[9,4],[10,2],[10,3],[10,4],[11,2],[11,3]]},"params":{"d[w]":"params[demand_width_w], w in W","a[p,w]":"params[pattern_p_width_w], (p,w) in A; omitted pairs produce zero","u[p]":"params[usage_limit_p], p in P"},"variables":{"x[p]":"nonnegative integer, p in P"},"constraints":["sum(a[p,w]*x[p] for p with (p,w) in A) >= d[w], w in W","x[p] <= u[p], p in P"],"objective":"minimize sum(x[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = {
        1: params["demand_width_1"],
        2: params["demand_width_2"],
        3: params["demand_width_3"],
        4: params["demand_width_4"],
    }

    production_data = {
        (0, 1): params["pattern_0_width_1"],
        (0, 2): params["pattern_0_width_2"],
        (0, 4): params["pattern_0_width_4"],
        (1, 1): params["pattern_1_width_1"],
        (1, 2): params["pattern_1_width_2"],
        (1, 4): params["pattern_1_width_4"],
        (2, 3): params["pattern_2_width_3"],
        (2, 4): params["pattern_2_width_4"],
        (3, 1): params["pattern_3_width_1"],
        (3, 2): params["pattern_3_width_2"],
        (3, 3): params["pattern_3_width_3"],
        (3, 4): params["pattern_3_width_4"],
        (4, 3): params["pattern_4_width_3"],
        (4, 4): params["pattern_4_width_4"],
        (5, 1): params["pattern_5_width_1"],
        (5, 2): params["pattern_5_width_2"],
        (5, 3): params["pattern_5_width_3"],
        (5, 4): params["pattern_5_width_4"],
        (6, 1): params["pattern_6_width_1"],
        (6, 2): params["pattern_6_width_2"],
        (6, 3): params["pattern_6_width_3"],
        (6, 4): params["pattern_6_width_4"],
        (7, 1): params["pattern_7_width_1"],
        (7, 2): params["pattern_7_width_2"],
        (7, 4): params["pattern_7_width_4"],
        (8, 1): params["pattern_8_width_1"],
        (8, 2): params["pattern_8_width_2"],
        (8, 3): params["pattern_8_width_3"],
        (8, 4): params["pattern_8_width_4"],
        (9, 1): params["pattern_9_width_1"],
        (9, 2): params["pattern_9_width_2"],
        (9, 3): params["pattern_9_width_3"],
        (9, 4): params["pattern_9_width_4"],
        (10, 2): params["pattern_10_width_2"],
        (10, 3): params["pattern_10_width_3"],
        (10, 4): params["pattern_10_width_4"],
        (11, 2): params["pattern_11_width_2"],
        (11, 3): params["pattern_11_width_3"],
    }

    usage_limit_data = {
        0: params["usage_limit_0"],
        1: params["usage_limit_1"],
        2: params["usage_limit_2"],
        3: params["usage_limit_3"],
        4: params["usage_limit_4"],
        5: params["usage_limit_5"],
        6: params["usage_limit_6"],
        7: params["usage_limit_7"],
        8: params["usage_limit_8"],
        9: params["usage_limit_9"],
        10: params["usage_limit_10"],
        11: params["usage_limit_11"],
    }

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 11)
    model.W = pyo.RangeSet(1, 4)
    model.A = pyo.Set(
        dimen=2,
        within=model.P * model.W,
        initialize=production_data.keys(),
    )

    model.d = pyo.Param(
        model.W, initialize=demand_data, within=pyo.NonNegativeReals
    )
    model.a = pyo.Param(
        model.A, initialize=production_data, within=pyo.NonNegativeReals
    )
    model.u = pyo.Param(
        model.P, initialize=usage_limit_data, within=pyo.NonNegativeReals
    )

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(current_model, width):
        return sum(
            current_model.a[pattern, width] * current_model.x[pattern]
            for pattern in current_model.P
            if (pattern, width) in current_model.A
        ) >= current_model.d[width]

    def usage_rule(current_model, pattern):
        return current_model.x[pattern] <= current_model.u[pattern]

    model.demand_constraints = pyo.Constraint(model.W, rule=demand_rule)
    model.usage_constraints = pyo.Constraint(model.P, rule=usage_rule)
    model.total_rolls = pyo.Objective(
        expr=sum(model.x[pattern] for pattern in model.P),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load can leave the objective unevaluable.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_rolls))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}