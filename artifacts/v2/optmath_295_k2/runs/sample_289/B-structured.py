# IR: {"sets":{"P":[0,1,2,3],"A":[0,1,2,3,4],"F":"complete set of forbidden assignment pairs, required as structural data"},"params":{"cost":"4x5 assignment-cost matrix","exactly_assignments":"exact assignment count","noe_forbidden_pairs_count":"required cardinality of F"},"variables":{"x[p,a]":"binary"},"constraints":["sum(x[p,a] for a in A)<=1 for each p in P","sum(x[p,a] for p in P)<=1 for each a in A","sum(x[p,a] for p in P for a in A)==exactly_assignments","x[p,a]+x[q,b]<=1 for each ((p,a),(q,b)) in F"],"objective":"minimize sum(cost[p,a]*x[p,a] for p in P for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    exactly_assignments = params["exactly_assignments"]
    forbidden_count = params["noe_forbidden_pairs_count"]

    peaks = range(4)
    amino_acids = range(5)

    specified_pairs = {
        ((0, 0), (3, 3)),
        ((0, 0), (3, 4)),
        ((0, 1), (3, 3)),
        ((0, 1), (3, 4)),
    }

    # The problem supplies only these four forbidden pairs, not the full
    # collection. Its cardinality does not determine the missing identities.
    # Consequently, no script can uniquely recover the requested model from
    # the three listed parameters alone. Do not invent the missing constraints
    # or report a solution of a relaxation as the requested optimum.
    #
    # A complete instance can supply the missing structural information as:
    # params["noe_forbidden_pairs"] = [
    #     ((peak, amino_acid), (other_peak, other_amino_acid)), ...
    # ]
    supplied_pairs = params.get("noe_forbidden_pairs")
    if supplied_pairs is None:
        if forbidden_count != len(specified_pairs):
            return {"objective": None, "status": "incomplete_noe_data"}
        supplied_pairs = specified_pairs

    forbidden_pairs = set()
    for pair in supplied_pairs:
        if len(pair) != 2:
            return {"objective": None, "status": "invalid_noe_pairs"}

        first, second = pair
        if len(first) != 2 or len(second) != 2:
            return {"objective": None, "status": "invalid_noe_pairs"}

        first = tuple(first)
        second = tuple(second)
        for peak, acid in (first, second):
            if peak not in peaks or acid not in amino_acids:
                return {"objective": None, "status": "invalid_noe_pairs"}

        canonical_pair = tuple(sorted((first, second)))
        if canonical_pair in forbidden_pairs:
            return {"objective": None, "status": "duplicate_noe_pairs"}
        forbidden_pairs.add(canonical_pair)

    if len(forbidden_pairs) != forbidden_count:
        return {"objective": None, "status": "noe_pair_count_mismatch"}
    if not specified_pairs.issubset(forbidden_pairs):
        return {"objective": None, "status": "missing_specified_noe_pairs"}

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=peaks, ordered=True)
    model.A = pyo.Set(initialize=amino_acids, ordered=True)
    model.assignment_cost = pyo.Param(
        model.P,
        model.A,
        initialize={
            (peak, acid): cost[peak][acid]
            for peak in peaks
            for acid in amino_acids
        },
    )
    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def peak_capacity_rule(current, peak):
        return sum(current.x[peak, acid] for acid in current.A) <= 1

    def amino_capacity_rule(current, acid):
        return sum(current.x[peak, acid] for peak in current.P) <= 1

    model.peak_capacity = pyo.Constraint(model.P, rule=peak_capacity_rule)
    model.amino_capacity = pyo.Constraint(model.A, rule=amino_capacity_rule)
    model.assignment_total = pyo.Constraint(
        expr=sum(
            model.x[peak, acid] for peak in model.P for acid in model.A
        ) == exactly_assignments
    )

    model.noe_constraints = pyo.ConstraintList()
    for (peak, acid), (other_peak, other_acid) in sorted(forbidden_pairs):
        model.noe_constraints.add(
            model.x[peak, acid] + model.x[other_peak, other_acid] <= 1
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, acid] * model.x[peak, acid]
            for peak in model.P
            for acid in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A solve without a loadable solution can raise RuntimeError.
        # Success is determined exclusively by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective_value"}

    return {"objective": obj_val, "status": "optimal"}