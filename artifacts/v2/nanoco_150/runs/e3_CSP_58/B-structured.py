# IR: {"sets":{"I":"range(len(segment_lengths))","R":"range(sum(demands))"},"params":{"stock_length":"params['stock_length']","segment_lengths":"params['segment_lengths']","demands":"params['demands']"},"variables":{"cut[i,r]":"nonnegative integer, upper bound demands[i]","used[r]":"binary"},"constraints":["For each i: sum_r cut[i,r] = demands[i]","For each r: sum_i segment_lengths[i]*cut[i,r] <= stock_length*used[r]","For consecutive reels r,r+1: used[r] >= used[r+1]"],"objective":"minimize sum_r used[r]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock_length = params["stock_length"]
    segment_lengths = list(params["segment_lengths"])
    demands = list(params["demands"])

    if len(segment_lengths) != len(demands):
        raise ValueError("segment_lengths and demands must have equal lengths.")
    if stock_length <= 0:
        raise ValueError("stock_length must be positive.")
    if any(length <= 0 for length in segment_lengths):
        raise ValueError("segment_lengths must be positive.")
    if any(demand < 0 or int(demand) != demand for demand in demands):
        raise ValueError("demands must be nonnegative integers.")

    reel_limit = int(sum(demands))

    model = pyo.ConcreteModel()
    model.segment_types = pyo.Set(
        initialize=range(len(segment_lengths)), ordered=True
    )
    model.reels = pyo.Set(initialize=range(reel_limit), ordered=True)

    model.cut = pyo.Var(
        model.segment_types,
        model.reels,
        domain=pyo.NonNegativeIntegers,
        bounds=lambda instance, i, r: (0, demands[i]),
    )
    model.used = pyo.Var(model.reels, domain=pyo.Binary)

    def demand_rule(instance, i):
        return (
            pyo.quicksum(instance.cut[i, r] for r in instance.reels)
            == demands[i]
        )

    model.exact_demand = pyo.Constraint(
        model.segment_types, rule=demand_rule
    )

    def capacity_rule(instance, r):
        return (
            pyo.quicksum(
                segment_lengths[i] * instance.cut[i, r]
                for i in instance.segment_types
            )
            <= stock_length * instance.used[r]
        )

    model.reel_capacity = pyo.Constraint(model.reels, rule=capacity_rule)

    def ordering_rule(instance, r):
        if r + 1 >= reel_limit:
            return pyo.Constraint.Skip
        return instance.used[r] >= instance.used[r + 1]

    model.reel_ordering = pyo.Constraint(model.reels, rule=ordering_rule)

    model.total_reels = pyo.Objective(
        expr=pyo.quicksum(model.used[r] for r in model.reels),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_reels))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}