# IR: {"sets":{"I":[1,2,3,4],"J":"range(max(1,sum(D[i] for i in I)))"},"params":{"B":"params['bolt_length'], positive real","L[i]":"params['strip_length_L'+str(i)], positive real","D[i]":"params['demand_D'+str(i)], nonnegative integer"},"variables":{"x[i,j]":"nonnegative integer, upper bound D[i]","y[j]":"binary"},"constraints":["For each i: sum(x[i,j] for j in J) == D[i]","For each j: sum(L[i]*x[i,j] for i in I) <= B*y[j]"],"objective":"minimize sum(y[j] for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.strip_types = pyo.RangeSet(1, 4)

    model.bolt_length = pyo.Param(
        initialize=params["bolt_length"],
        within=pyo.PositiveReals,
    )

    model.strip_lengths = pyo.Param(
        model.strip_types,
        initialize={
            1: params["strip_length_L1"],
            2: params["strip_length_L2"],
            3: params["strip_length_L3"],
            4: params["strip_length_L4"],
        },
        within=pyo.PositiveReals,
    )

    model.strip_demands = pyo.Param(
        model.strip_types,
        initialize={
            1: params["demand_D1"],
            2: params["demand_D2"],
            3: params["demand_D3"],
            4: params["demand_D4"],
        },
        within=pyo.NonNegativeIntegers,
    )

    # One bolt per demanded strip is a sufficient candidate-bolt bound.
    # Retain one candidate for the zero-demand case; it can remain unused.
    candidate_count = max(
        1,
        int(
            sum(
                pyo.value(model.strip_demands[strip_type])
                for strip_type in model.strip_types
            )
        ),
    )
    model.bolts = pyo.Set(
        initialize=range(candidate_count),
        ordered=True,
    )

    def piece_bounds(instance, strip_type, bolt):
        return 0, instance.strip_demands[strip_type]

    model.pieces = pyo.Var(
        model.strip_types,
        model.bolts,
        domain=pyo.NonNegativeIntegers,
        bounds=piece_bounds,
    )
    model.bolt_used = pyo.Var(
        model.bolts,
        domain=pyo.Binary,
    )

    def demand_rule(instance, strip_type):
        return (
            sum(
                instance.pieces[strip_type, bolt]
                for bolt in instance.bolts
            )
            == instance.strip_demands[strip_type]
        )

    model.exact_demand = pyo.Constraint(
        model.strip_types,
        rule=demand_rule,
    )

    def capacity_rule(instance, bolt):
        return (
            sum(
                instance.strip_lengths[strip_type]
                * instance.pieces[strip_type, bolt]
                for strip_type in instance.strip_types
            )
            <= instance.bolt_length * instance.bolt_used[bolt]
        )

    model.bolt_capacity = pyo.Constraint(
        model.bolts,
        rule=capacity_rule,
    )

    model.bolt_count = pyo.Objective(
        expr=sum(model.bolt_used[bolt] for bolt in model.bolts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.bolt_count))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}