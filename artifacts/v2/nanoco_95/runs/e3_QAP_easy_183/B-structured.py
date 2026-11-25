# IR: {"sets":{"D":"range(params['n_departments'])","Z":"range(params['n_zones'])","P":"{(i,j) in D x D: i<j}"},"params":{"n_departments":"params['n_departments']","n_zones":"params['n_zones']","flow":"params['flow']; nested matrix, row-major flat matrix, or tuple-keyed mapping","distance":"params['distance']; nested matrix, row-major flat matrix, or tuple-keyed mapping; authoritative distances","x_coords":"params['x_coords']; zone coordinate metadata","y_coords":"params['y_coords']; zone coordinate metadata"},"variables":{"assign[i,k]":"binary, i in D and k in Z","joint[i,j,k,l]":"continuous in [0,1], (i,j) in P and k,l in Z"},"constraints":["For each i in D: sum_k assign[i,k] = 1","For each k in Z: sum_i assign[i,k] = 1","For each (i,j) in P and k,l in Z: joint[i,j,k,l] <= assign[i,k]","For each (i,j) in P and k,l in Z: joint[i,j,k,l] <= assign[j,l]","For each (i,j) in P and k,l in Z: joint[i,j,k,l] >= assign[i,k] + assign[j,l] - 1"],"objective":"Minimize sum_{(i,j) in P,k,l in Z} flow[i,j]*distance[k,l]*joint[i,j,k,l]; count each unordered department pair once"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _matrix_entry(data, row, column, width):
    """Read nested, row-major flattened, or tuple-keyed matrix data."""
    if isinstance(data, Mapping) and (row, column) in data:
        return data[row, column]

    row_entry = data[row]
    if hasattr(row_entry, "__getitem__") and not isinstance(
        row_entry, (str, bytes)
    ):
        return row_entry[column]

    return data[row * width + column]


def solve(params):
    model = pyo.ConcreteModel()

    model.department_count = pyo.Param(
        initialize=params["n_departments"],
        within=pyo.PositiveIntegers,
    )
    model.zone_count = pyo.Param(
        initialize=params["n_zones"],
        within=pyo.PositiveIntegers,
    )

    department_count = int(pyo.value(model.department_count))
    zone_count = int(pyo.value(model.zone_count))

    model.D = pyo.Set(
        initialize=range(department_count),
        ordered=True,
    )
    model.Z = pyo.Set(
        initialize=range(zone_count),
        ordered=True,
    )
    model.P = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.D
            for j in model.D
            if i < j
        ],
        ordered=True,
    )

    model.flow_data = pyo.Param(
        model.D,
        model.D,
        initialize=lambda mdl, i, j: _matrix_entry(
            params["flow"], i, j, department_count
        ),
        within=pyo.NonNegativeReals,
    )
    model.distance_data = pyo.Param(
        model.Z,
        model.Z,
        initialize=lambda mdl, k, ell: _matrix_entry(
            params["distance"], k, ell, zone_count
        ),
        within=pyo.NonNegativeReals,
    )

    # The supplied distance matrix is authoritative; retain coordinates
    # as metadata without recomputing or rounding distances.
    model.zone_x = pyo.Param(
        model.Z,
        initialize=lambda mdl, k: params["x_coords"][k],
        within=pyo.Reals,
    )
    model.zone_y = pyo.Param(
        model.Z,
        initialize=lambda mdl, k: params["y_coords"][k],
        within=pyo.Reals,
    )

    model.assign = pyo.Var(
        model.D,
        model.Z,
        domain=pyo.Binary,
    )
    model.joint = pyo.Var(
        model.P,
        model.Z,
        model.Z,
        domain=pyo.UnitInterval,
    )

    model.department_assignment = pyo.Constraint(
        model.D,
        rule=lambda mdl, i: (
            sum(mdl.assign[i, k] for k in mdl.Z) == 1
        ),
    )
    model.zone_occupancy = pyo.Constraint(
        model.Z,
        rule=lambda mdl, k: (
            sum(mdl.assign[i, k] for i in mdl.D) == 1
        ),
    )

    model.joint_first_upper = pyo.Constraint(
        model.P,
        model.Z,
        model.Z,
        rule=lambda mdl, i, j, k, ell: (
            mdl.joint[i, j, k, ell] <= mdl.assign[i, k]
        ),
    )
    model.joint_second_upper = pyo.Constraint(
        model.P,
        model.Z,
        model.Z,
        rule=lambda mdl, i, j, k, ell: (
            mdl.joint[i, j, k, ell] <= mdl.assign[j, ell]
        ),
    )
    model.joint_lower = pyo.Constraint(
        model.P,
        model.Z,
        model.Z,
        rule=lambda mdl, i, j, k, ell: (
            mdl.joint[i, j, k, ell]
            >= mdl.assign[i, k] + mdl.assign[j, ell] - 1
        ),
    )

    model.total_missed_synergy = pyo.Objective(
        expr=sum(
            model.flow_data[i, j]
            * model.distance_data[k, ell]
            * model.joint[i, j, k, ell]
            for i, j in model.P
            for k in model.Z
            for ell in model.Z
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_missed_synergy))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}