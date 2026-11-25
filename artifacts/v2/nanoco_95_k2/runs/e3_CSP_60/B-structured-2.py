# IR: {"sets":{"I":[1,2,3,4],"J":"1..max(1,sum_i D[i])"},"params":{"B":"params['bolt_length']","L[i]":"params['strip_length_L'+str(i)]","D[i]":"params['demand_D'+str(i)]"},"variables":{"x[i,j]":"nonnegative integer; strips of type i cut from bolt j","y[j]":"binary; whether bolt j is used"},"constraints":["sum_j x[i,j] = D[i] for each i","sum_i L[i]*x[i,j] <= B*y[j] for each j","x[i,j] <= D[i]*y[j] for each i,j","y[j] >= y[j+1] for each consecutive pair of bolts"],"objective":"minimize sum_j y[j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bolt_length = params["bolt_length"]
    strip_lengths = {
        1: params["strip_length_L1"],
        2: params["strip_length_L2"],
        3: params["strip_length_L3"],
        4: params["strip_length_L4"],
    }
    demands = {
        1: params["demand_D1"],
        2: params["demand_D2"],
        3: params["demand_D3"],
        4: params["demand_D4"],
    }

    if bolt_length <= 0:
        raise ValueError("bolt_length must be positive.")
    if any(length <= 0 for length in strip_lengths.values()):
        raise ValueError("Strip lengths must be positive.")
    if any(quantity < 0 or int(quantity) != quantity
           for quantity in demands.values()):
        raise ValueError("Demands must be nonnegative integers.")

    # One candidate bolt per required strip suffices whenever feasible.
    # Retain one candidate for the zero-demand case.
    candidate_count = max(1, int(sum(demands.values())))

    model = pyo.ConcreteModel()
    model.strip_types = pyo.RangeSet(1, 4)
    model.bolts = pyo.RangeSet(1, candidate_count)

    model.bolt_capacity = pyo.Param(initialize=bolt_length)
    model.strip_lengths = pyo.Param(
        model.strip_types, initialize=strip_lengths
    )
    model.required_quantities = pyo.Param(
        model.strip_types, initialize=demands
    )

    model.cut_counts = pyo.Var(
        model.strip_types, model.bolts,
        domain=pyo.NonNegativeIntegers,
    )
    model.bolt_used = pyo.Var(model.bolts, domain=pyo.Binary)

    def demand_rule(model, strip_type):
        return (
            sum(model.cut_counts[strip_type, bolt] for bolt in model.bolts)
            == model.required_quantities[strip_type]
        )

    model.exact_demand = pyo.Constraint(
        model.strip_types, rule=demand_rule
    )

    def capacity_rule(model, bolt):
        return (
            sum(
                model.strip_lengths[strip_type]
                * model.cut_counts[strip_type, bolt]
                for strip_type in model.strip_types
            )
            <= model.bolt_capacity * model.bolt_used[bolt]
        )

    model.bolt_capacity_limits = pyo.Constraint(
        model.bolts, rule=capacity_rule
    )

    def activation_rule(model, strip_type, bolt):
        return (
            model.cut_counts[strip_type, bolt]
            <= model.required_quantities[strip_type]
            * model.bolt_used[bolt]
        )

    model.cut_activation = pyo.Constraint(
        model.strip_types, model.bolts, rule=activation_rule
    )

    def ordering_rule(model, bolt):
        if bolt == candidate_count:
            return pyo.Constraint.Skip
        return model.bolt_used[bolt] >= model.bolt_used[bolt + 1]

    model.bolt_ordering = pyo.Constraint(
        model.bolts, rule=ordering_rule
    )

    model.total_bolts = pyo.Objective(
        expr=sum(model.bolt_used[bolt] for bolt in model.bolts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrieval alone determines success.
    try:
        obj_val = float(pyo.value(model.total_bolts))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}