import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    bar_length = params["bar_length"]
    order_28 = params["order_28"]
    order_38 = params["order_38"]
    order_21 = params["order_21"]
    piece_length_28 = params["piece_length_28"]
    piece_length_38 = params["piece_length_38"]
    piece_length_21 = params["piece_length_21"]

    piece_types = ["28", "38", "21"]
    piece_lengths = {
        "28": piece_length_28,
        "38": piece_length_38,
        "21": piece_length_21,
    }
    demands = {
        "28": order_28,
        "38": order_38,
        "21": order_21,
    }

    total_length = (
        order_28 * piece_length_28
        + order_38 * piece_length_38
        + order_21 * piece_length_21
    )
    max_bars = int(total_length // bar_length) + order_28 + order_38 + order_21 + 1

    model = pyo.ConcreteModel()
    model.bars = pyo.RangeSet(1, max_bars)
    model.pieces = pyo.Set(initialize=piece_types)

    model.x = pyo.Var(model.bars, model.pieces, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.bars, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=pyo.quicksum(model.y[i] for i in model.bars),
        sense=pyo.minimize,
    )

    def length_rule(m, i):
        return (
            pyo.quicksum(m.x[i, p] * piece_lengths[p] for p in m.pieces)
            <= bar_length * m.y[i]
        )
    model.length_constraint = pyo.Constraint(model.bars, rule=length_rule)

    def demand_rule(m, p):
        return pyo.quicksum(m.x[i, p] for i in m.bars) >= demands[p]
    model.demand_constraint = pyo.Constraint(model.pieces, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}