import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Sets
    patterns = list(range(12))
    widths = [1, 2, 3, 4]

    # Usage variables (integer, nonnegative)
    model.x = pyo.Var(patterns, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total number of rolls cut
    model.total_rolls = pyo.Objective(
        expr=sum(model.x[p] for p in patterns),
        sense=pyo.minimize,
    )

    # Demand constraints for each width
    model.demand_1 = pyo.Constraint(
        expr=(
            params["pattern_0_width_1"] * model.x[0]
            + params["pattern_1_width_1"] * model.x[1]
            + params["pattern_3_width_1"] * model.x[3]
            + params["pattern_5_width_1"] * model.x[5]
            + params["pattern_6_width_1"] * model.x[6]
            + params["pattern_7_width_1"] * model.x[7]
            + params["pattern_8_width_1"] * model.x[8]
            + params["pattern_9_width_1"] * model.x[9]
            >= params["demand_width_1"]
        )
    )

    model.demand_2 = pyo.Constraint(
        expr=(
            params["pattern_0_width_2"] * model.x[0]
            + params["pattern_1_width_2"] * model.x[1]
            + params["pattern_3_width_2"] * model.x[3]
            + params["pattern_5_width_2"] * model.x[5]
            + params["pattern_6_width_2"] * model.x[6]
            + params["pattern_7_width_2"] * model.x[7]
            + params["pattern_8_width_2"] * model.x[8]
            + params["pattern_9_width_2"] * model.x[9]
            + params["pattern_10_width_2"] * model.x[10]
            + params["pattern_11_width_2"] * model.x[11]
            >= params["demand_width_2"]
        )
    )

    model.demand_3 = pyo.Constraint(
        expr=(
            params["pattern_2_width_3"] * model.x[2]
            + params["pattern_3_width_3"] * model.x[3]
            + params["pattern_4_width_3"] * model.x[4]
            + params["pattern_5_width_3"] * model.x[5]
            + params["pattern_6_width_3"] * model.x[6]
            + params["pattern_8_width_3"] * model.x[8]
            + params["pattern_9_width_3"] * model.x[9]
            + params["pattern_10_width_3"] * model.x[10]
            + params["pattern_11_width_3"] * model.x[11]
            >= params["demand_width_3"]
        )
    )

    model.demand_4 = pyo.Constraint(
        expr=(
            params["pattern_0_width_4"] * model.x[0]
            + params["pattern_1_width_4"] * model.x[1]
            + params["pattern_2_width_4"] * model.x[2]
            + params["pattern_3_width_4"] * model.x[3]
            + params["pattern_4_width_4"] * model.x[4]
            + params["pattern_5_width_4"] * model.x[5]
            + params["pattern_6_width_4"] * model.x[6]
            + params["pattern_7_width_4"] * model.x[7]
            + params["pattern_8_width_4"] * model.x[8]
            + params["pattern_9_width_4"] * model.x[9]
            + params["pattern_10_width_4"] * model.x[10]
            >= params["demand_width_4"]
        )
    )

    # Usage limit constraints
    model.limit_0 = pyo.Constraint(expr=model.x[0] <= params["usage_limit_0"])
    model.limit_1 = pyo.Constraint(expr=model.x[1] <= params["usage_limit_1"])
    model.limit_2 = pyo.Constraint(expr=model.x[2] <= params["usage_limit_2"])
    model.limit_3 = pyo.Constraint(expr=model.x[3] <= params["usage_limit_3"])
    model.limit_4 = pyo.Constraint(expr=model.x[4] <= params["usage_limit_4"])
    model.limit_5 = pyo.Constraint(expr=model.x[5] <= params["usage_limit_5"])
    model.limit_6 = pyo.Constraint(expr=model.x[6] <= params["usage_limit_6"])
    model.limit_7 = pyo.Constraint(expr=model.x[7] <= params["usage_limit_7"])
    model.limit_8 = pyo.Constraint(expr=model.x[8] <= params["usage_limit_8"])
    model.limit_9 = pyo.Constraint(expr=model.x[9] <= params["usage_limit_9"])
    model.limit_10 = pyo.Constraint(expr=model.x[10] <= params["usage_limit_10"])
    model.limit_11 = pyo.Constraint(expr=model.x[11] <= params["usage_limit_11"])

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.total_rolls))
    return {"objective": obj_val, "status": "optimal"}