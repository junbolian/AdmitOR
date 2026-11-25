# IR: {"sets":{"P":[0,1,2,3],"A":[0,1,2,3,4],"F":"complete set of forbidden pairs ((p,a),(q,b)); must be explicitly specified"},"params":{"cost":"params['cost'], a 4x5 matrix","exactly_assignments":"params['exactly_assignments']","noe_forbidden_pairs_count":"params['noe_forbidden_pairs_count'], frozen cardinality of F"},"variables":{"x[p,a]":"binary"},"constraints":["sum_a x[p,a] <= 1 for each p","sum_p x[p,a] <= 1 for each a","sum_p sum_a x[p,a] == exactly_assignments","x[p,a] + x[q,b] <= 1 for each ((p,a),(q,b)) in F"],"objective":"minimize sum_p sum_a cost[p,a]*x[p,a]"}
#
# The supplied problem is underspecified: it gives four explicit forbidden
# pairs, but not the complete list. A cardinality does not identify that list.
# There is no justified way to reconstruct the remaining restrictions.
# This implementation therefore does not invent them. An optional
# params["noe_forbidden_pairs"] can supply the missing structural information.
# With only the three listed parameters, an incomplete specification is
# reported rather than an incorrect optimum.

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    required = params["exactly_assignments"]
    forbidden_count = operator.index(params["noe_forbidden_pairs_count"])

    peaks = tuple(range(4))
    amino_acids = tuple(range(5))

    if forbidden_count < 0:
        return {"objective": None, "status": "invalid_noe_count"}

    if len(cost) != len(peaks) or any(
        len(row) != len(amino_acids) for row in cost
    ):
        return {"objective": None, "status": "invalid_cost_shape"}

    explicitly_stated_pairs = (
        ((0, 0), (3, 3)),
        ((0, 0), (3, 4)),
        ((0, 1), (3, 3)),
        ((0, 1), (3, 4)),
    )
    supplied_pairs = params.get("noe_forbidden_pairs")

    if supplied_pairs is None:
        if forbidden_count != len(explicitly_stated_pairs):
            return {
                "objective": None,
                "status": "incomplete_noe_specification",
            }
        supplied_pairs = explicitly_stated_pairs

    forbidden_pairs = []
    seen = set()

    for entry in supplied_pairs:
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            return {"objective": None, "status": "invalid_noe_pair"}

        left, right = entry
        if any(
            not isinstance(endpoint, (tuple, list)) or len(endpoint) != 2
            for endpoint in (left, right)
        ):
            return {"objective": None, "status": "invalid_noe_pair"}

        peak_left, acid_left = left
        peak_right, acid_right = right
        if (
            peak_left not in peaks
            or peak_right not in peaks
            or acid_left not in amino_acids
            or acid_right not in amino_acids
        ):
            return {"objective": None, "status": "invalid_noe_index"}

        canonical = tuple(sorted((tuple(left), tuple(right))))
        if canonical in seen:
            return {"objective": None, "status": "duplicate_noe_pair"}

        seen.add(canonical)
        forbidden_pairs.append(
            (peak_left, acid_left, peak_right, acid_right)
        )

    if len(forbidden_pairs) != forbidden_count:
        return {"objective": None, "status": "noe_count_mismatch"}

    if any(
        tuple(sorted(pair)) not in seen
        for pair in explicitly_stated_pairs
    ):
        return {"objective": None, "status": "missing_stated_noe_pair"}

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
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=required, within=pyo.Reals
    )
    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def peak_capacity_rule(instance, peak):
        return sum(instance.x[peak, acid] for acid in instance.A) <= 1

    def acid_capacity_rule(instance, acid):
        return sum(instance.x[peak, acid] for peak in instance.P) <= 1

    model.peak_capacity = pyo.Constraint(
        model.P, rule=peak_capacity_rule
    )
    model.acid_capacity = pyo.Constraint(
        model.A, rule=acid_capacity_rule
    )
    model.assignment_total = pyo.Constraint(
        expr=sum(
            model.x[peak, acid]
            for peak in model.P
            for acid in model.A
        )
        == model.required_assignments
    )

    model.noe_restrictions = pyo.ConstraintList()
    for peak_left, acid_left, peak_right, acid_right in forbidden_pairs:
        model.noe_restrictions.add(
            model.x[peak_left, acid_left]
            + model.x[peak_right, acid_right]
            <= 1
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}