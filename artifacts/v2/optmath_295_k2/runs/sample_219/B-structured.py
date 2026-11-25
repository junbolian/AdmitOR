# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4],"R":"normalized records from params['noe_thresholds']"},"params":{"cost_matrix":"assignment costs indexed by (i,j)","total_assignments":"exact assignment count","noe_thresholds":"numeric bounds indexed by amino-acid pairs (j,l), assignment quadruples (i,j,k,l), or explicit records; pair indices refer to peaks 1 and 3; records with distance instead prohibit coexistence when distance >= threshold"},"variables":{"x[i,j]":"binary"},"constraints":["For each j in J: sum_i x[i,j] <= 1.","For each i in I: sum_j x[i,j] <= 1.","sum_i,j x[i,j] == total_assignments.","For each normalized record (i,j,k,l,b): x[i,j] + x[k,l] <= b."],"objective":"minimize sum_i,j cost_matrix[i][j] * x[i,j]"}

import ast
import math
from collections.abc import Mapping, Sequence
from numbers import Integral

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _is_sequence(value):
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _parse_key(key):
    if isinstance(key, str):
        try:
            key = ast.literal_eval(key)
        except (ValueError, SyntaxError):
            pieces = key.split(",")
            if len(pieces) not in (2, 4):
                raise ValueError("Invalid NOE key.")
            key = tuple(int(piece.strip()) for piece in pieces)

    if isinstance(key, Integral):
        return int(key)

    if _is_sequence(key) and len(key) in (2, 4):
        if not all(isinstance(index, Integral) for index in key):
            raise ValueError("NOE indices must be integers.")
        return tuple(int(index) for index in key)

    raise ValueError("Invalid NOE key.")


def _normalize_noe(raw):
    """
    Supported NOE inputs:

    * A 5-by-5 numeric matrix: entry [j][l] bounds x[1,j] + x[3,l].
    * A mapping {(j, l): bound}, or {(i, j, k, l): bound}.
      String representations of these tuple keys are also accepted.
    * A nested mapping {j: {l: bound}} for peaks 1 and 3.
    * Records with peak_i, amino_j, peak_k, amino_l, and threshold
      (or bound). Omitting peak_i and peak_k selects peaks 1 and 3.
    * Sparse rows [j, l, bound].

    Numeric entries without distances are supplied inequality bounds.
    Physical distances are not inferred from amino-acid indices. If a
    record explicitly includes distance and threshold, its assignments
    are incompatible when distance >= threshold.

    Empty inputs impose no NOE constraints.
    """
    normalized = []

    def add_record(indices, specification):
        if len(indices) == 2:
            peak_i, amino_j, peak_k, amino_l = (
                1, indices[0], 3, indices[1]
            )
        else:
            peak_i, amino_j, peak_k, amino_l = indices

        if (
            peak_i not in range(4)
            or peak_k not in range(4)
            or amino_j not in range(5)
            or amino_l not in range(5)
        ):
            raise ValueError("NOE index outside its index set.")

        if isinstance(specification, Mapping):
            if "distance" in specification:
                distance = float(specification["distance"])
                threshold = float(specification["threshold"])
                if (
                    not math.isfinite(distance)
                    or not math.isfinite(threshold)
                    or distance < 0
                    or threshold < 0
                ):
                    raise ValueError("Invalid NOE distance or threshold.")
                if distance < threshold:
                    return
                bound = 1
            elif "bound" in specification:
                bound = float(specification["bound"])
            else:
                bound = float(specification["threshold"])
        else:
            bound = float(specification)

        if not math.isfinite(bound):
            raise ValueError("NOE bounds must be finite.")

        normalized.append(
            (peak_i, amino_j, peak_k, amino_l, bound)
        )

    def add_explicit_record(record):
        indices = (
            record.get("peak_i", 1),
            record["amino_j"],
            record.get("peak_k", 3),
            record["amino_l"],
        )
        if not all(isinstance(index, Integral) for index in indices):
            raise ValueError("NOE indices must be integers.")
        add_record(tuple(int(index) for index in indices), record)

    if isinstance(raw, Mapping):
        if "amino_j" in raw and "amino_l" in raw:
            add_explicit_record(raw)
        else:
            for key, specification in raw.items():
                parsed_key = _parse_key(key)
                if isinstance(parsed_key, int):
                    if isinstance(specification, Mapping):
                        entries = specification.items()
                    elif _is_sequence(specification):
                        entries = enumerate(specification)
                    else:
                        raise ValueError("Invalid nested NOE data.")
                    for amino_l, bound in entries:
                        parsed_amino_l = _parse_key(amino_l)
                        if not isinstance(parsed_amino_l, int):
                            raise ValueError("Invalid amino-acid index.")
                        add_record((parsed_key, parsed_amino_l), bound)
                else:
                    add_record(parsed_key, specification)

    elif _is_sequence(raw):
        is_matrix = (
            len(raw) == 5
            and all(_is_sequence(row) and len(row) == 5 for row in raw)
        )
        if is_matrix:
            for amino_j, row in enumerate(raw):
                for amino_l, bound in enumerate(row):
                    add_record((amino_j, amino_l), bound)
        else:
            for record in raw:
                if isinstance(record, Mapping):
                    add_explicit_record(record)
                elif _is_sequence(record) and len(record) == 3:
                    indices = _parse_key(record[:2])
                    add_record(indices, record[2])
                else:
                    raise ValueError("Unsupported NOE record.")
    else:
        raise ValueError("Unsupported NOE input.")

    return normalized


def solve(params):
    cost_matrix = params["cost_matrix"]
    total_assignments = params["total_assignments"]
    noe_thresholds = params["noe_thresholds"]

    try:
        noe_records = _normalize_noe(noe_thresholds)
    except (ValueError, TypeError, KeyError, OverflowError):
        return {"objective": None, "status": "invalid_noe_data"}

    model = pyo.ConcreteModel()
    model.peaks = pyo.RangeSet(0, 3)
    model.amino_acids = pyo.RangeSet(0, 4)

    def cost_initializer(instance, peak, amino):
        if isinstance(cost_matrix, Mapping):
            if (peak, amino) in cost_matrix:
                return cost_matrix[peak, amino]
            string_key = str((peak, amino))
            if string_key in cost_matrix:
                return cost_matrix[string_key]
            row = cost_matrix[
                peak if peak in cost_matrix else str(peak)
            ]
        else:
            row = cost_matrix[peak]

        if isinstance(row, Mapping):
            return row[amino if amino in row else str(amino)]
        return row[amino]

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=cost_initializer,
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=total_assignments,
        within=pyo.Reals,
    )
    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def amino_capacity_rule(instance, amino):
        return sum(
            instance.x[peak, amino] for peak in instance.peaks
        ) <= 1

    model.amino_capacity = pyo.Constraint(
        model.amino_acids, rule=amino_capacity_rule
    )

    def peak_capacity_rule(instance, peak):
        return sum(
            instance.x[peak, amino]
            for amino in instance.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks, rule=peak_capacity_rule
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, amino]
            for peak in model.peaks
            for amino in model.amino_acids
        ) == model.required_assignments
    )

    model.noe_consistency = pyo.ConstraintList()
    for peak_i, amino_j, peak_k, amino_l, bound in noe_records:
        model.noe_consistency.add(
            model.x[peak_i, amino_j]
            + model.x[peak_k, amino_l]
            <= bound
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, amino] * model.x[peak, amino]
            for peak in model.peaks
            for amino in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    solve_error = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_error = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solve_failed" if solve_error else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}