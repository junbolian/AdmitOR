# IR: {"sets":{"I":"{0,1,2}","B":"{0,...,sum(d[i] for i in I)-1}"},"params":{"l":"params['segment_lengths']","d":"params['segment_demands']","L":"params['standard_rebar_length']"},"variables":{"x[b,i]":"nonnegative integer pieces of specification i cut from bar b","y[b]":"binary indicator that bar b is used"},"constraints":{"demand":"sum(x[b,i] for b in B) == d[i], for each i in I","capacity":"sum(l[i]*x[b,i] for i in I) <= L*y[b], for each b in B","link":"x[b,i] <= d[i]*y[b], for each b in B and i in I"},"objective":"minimize sum(y[b] for b in B)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    segment_lengths = params["segment_lengths"]
    segment_demands = params["segment_demands"]
    standard_rebar_length = params["standard_rebar_length"]

    if len(segment_lengths) != 3 or len(segment_demands) != 3:
        return {"objective": None, "status": "invalid_dimensions"}

    if standard_rebar_length <= 0 or any(
        length <= 0 for length in segment_lengths
    ):
        return {"objective": None, "status": "invalid_lengths"}

    if any(
        demand < 0 or demand != int(demand)
        for demand in segment_demands
    ):
        return {"objective": None, "status": "invalid_demands"}

    # One candidate bar per required piece is a sufficient upper bound.
    total_pieces = sum(int(demand) for demand in segment_demands)

    model = pyo.ConcreteModel()
    model.specifications = pyo.RangeSet(0, 2)
    model.bars = pyo.Set(initialize=range(total_pieces), ordered=True)

    model.cut_count = pyo.Var(
        model.bars,
        model.specifications,
        domain=pyo.NonNegativeIntegers,
    )
    model.bar_used = pyo.Var(model.bars, domain=pyo.Binary)

    def demand_rule(instance, spec):
        # Explicit symbolic starting value also supports zero total demand.
        return pyo.quicksum(
            instance.cut_count[bar, spec] for bar in instance.bars
        ) == segment_demands[spec]

    # An empty bar set would otherwise yield Boolean demand expressions.
    # A symbolic zero preserves the same equations in that case.
    model.zero_constant = pyo.Param(initialize=0, mutable=True)

    def symbolic_demand_rule(instance, spec):
        return (
            instance.zero_constant
            + pyo.quicksum(
                instance.cut_count[bar, spec] for bar in instance.bars
            )
            == segment_demands[spec]
        )

    model.required_quantities = pyo.Constraint(
        model.specifications,
        rule=symbolic_demand_rule,
    )

    def capacity_rule(instance, bar):
        return (
            pyo.quicksum(
                segment_lengths[spec] * instance.cut_count[bar, spec]
                for spec in instance.specifications
            )
            <= standard_rebar_length * instance.bar_used[bar]
        )

    model.bar_capacities = pyo.Constraint(model.bars, rule=capacity_rule)

    def linking_rule(instance, bar, spec):
        return (
            instance.cut_count[bar, spec]
            <= segment_demands[spec] * instance.bar_used[bar]
        )

    model.usage_links = pyo.Constraint(
        model.bars,
        model.specifications,
        rule=linking_rule,
    )

    model.total_bars = pyo.Objective(
        expr=pyo.quicksum(model.bar_used[bar] for bar in model.bars),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors must still propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_bars))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}