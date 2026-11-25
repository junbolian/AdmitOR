# IR: {"sets":{"T":["18","20","56"],"B":"range(sum(demand[t] for t in T))"},"params":{"stock_length":"params['standard_rebar_length']","demand":{"18":"params['demand_18']","20":"params['demand_20']","56":"params['demand_56']"},"length":{"18":"params['piece_length_18']","20":"params['piece_length_20']","56":"params['piece_length_56']"}},"variables":{"used[b]":"Binary","cuts[b,t]":"NonNegativeIntegers"},"constraints":["For each t: sum(cuts[b,t] for b in B) == demand[t]","For each b: sum(length[t]*cuts[b,t] for t in T) <= stock_length*used[b]"],"objective":"Minimize sum(used[b] for b in B)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock_length = params["standard_rebar_length"]
    demand = {
        "18": params["demand_18"],
        "20": params["demand_20"],
        "56": params["demand_56"],
    }
    length = {
        "18": params["piece_length_18"],
        "20": params["piece_length_20"],
        "56": params["piece_length_56"],
    }

    # One stock rebar per requested piece is a sufficient upper bound
    # whenever a feasible cutting plan exists.
    stock_count_bound = sum(demand.values())

    model = pyo.ConcreteModel()
    model.segment_types = pyo.Set(
        initialize=("18", "20", "56"), ordered=True
    )
    model.stock_indices = pyo.Set(
        initialize=range(stock_count_bound), ordered=True
    )

    model.used = pyo.Var(model.stock_indices, domain=pyo.Binary)
    model.cuts = pyo.Var(
        model.stock_indices,
        model.segment_types,
        domain=pyo.NonNegativeIntegers,
    )

    def exact_demand_rule(instance, segment_type):
        return (
            sum(
                instance.cuts[stock_index, segment_type]
                for stock_index in instance.stock_indices
            )
            == demand[segment_type]
        )

    model.exact_demand = pyo.Constraint(
        model.segment_types, rule=exact_demand_rule
    )

    def stock_capacity_rule(instance, stock_index):
        return (
            sum(
                length[segment_type]
                * instance.cuts[stock_index, segment_type]
                for segment_type in instance.segment_types
            )
            <= stock_length * instance.used[stock_index]
        )

    model.stock_capacity = pyo.Constraint(
        model.stock_indices, rule=stock_capacity_rule
    )

    model.total_rebars = pyo.Objective(
        expr=sum(
            model.used[stock_index]
            for stock_index in model.stock_indices
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions still propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Success depends solely on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_rebars))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}