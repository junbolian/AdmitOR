# IR: {
#   "sets": {"D": [0,1,2,3], "Z": [0,1,2,3], "P": "[(i,j) in D*D: i<j]", "A": "[(k,l) in Z*Z: k!=l]"},
#   "params": {"flow": ["flow_01","flow_02","flow_03","flow_12","flow_13","flow_23"], "distance": ["dist_01","dist_02","dist_03","dist_12","dist_13","dist_23"], "coordinate_metadata": ["coord_x0","coord_y0","coord_x1","coord_y1","coord_x2","coord_y2","coord_x3","coord_y3"]},
#   "variables": {"x[i,k]": "binary for (i,k) in D*Z", "y[i,j,k,l]": "continuous in [0,1] for (i,j) in P, (k,l) in A"},
#   "constraints": [
#     "sum(k in Z) x[i,k] = 1 for each i in D",
#     "sum(i in D) x[i,k] = 1 for each k in Z",
#     "sum(l in Z: l!=k) y[i,j,k,l] = x[i,k] for each (i,j) in P, k in Z",
#     "sum(k in Z: k!=l) y[i,j,k,l] = x[j,l] for each (i,j) in P, l in Z"
#   ],
#   "objective": "minimize sum((i,j) in P, (k,l) in A) flow[i,j]*distance[min(k,l),max(k,l)]*y[i,j,k,l]",
#   "distance_policy": "Use supplied integer distances; retain supplied coordinates as metadata."
# }

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow_data = {
        (0, 1): params["flow_01"],
        (0, 2): params["flow_02"],
        (0, 3): params["flow_03"],
        (1, 2): params["flow_12"],
        (1, 3): params["flow_13"],
        (2, 3): params["flow_23"],
    }
    distance_data = {
        (0, 1): params["dist_01"],
        (0, 2): params["dist_02"],
        (0, 3): params["dist_03"],
        (1, 2): params["dist_12"],
        (1, 3): params["dist_13"],
        (2, 3): params["dist_23"],
    }
    coordinate_x_data = {
        0: params["coord_x0"],
        1: params["coord_x1"],
        2: params["coord_x2"],
        3: params["coord_x3"],
    }
    coordinate_y_data = {
        0: params["coord_y0"],
        1: params["coord_y1"],
        2: params["coord_y2"],
        3: params["coord_y3"],
    }

    model = pyo.ConcreteModel()
    model.departments = pyo.Set(initialize=range(4), ordered=True)
    model.zones = pyo.Set(initialize=range(4), ordered=True)
    model.department_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (first, second)
            for first in range(4)
            for second in range(4)
            if first < second
        ],
    )
    model.zone_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(4)
            for destination in range(4)
            if origin != destination
        ],
    )

    model.flow = pyo.Param(
        model.department_pairs,
        initialize=flow_data,
        within=pyo.NonNegativeReals,
    )
    model.distance = pyo.Param(
        model.department_pairs,
        initialize=distance_data,
        within=pyo.NonNegativeReals,
    )
    model.coordinate_x = pyo.Param(
        model.zones, initialize=coordinate_x_data, within=pyo.Reals
    )
    model.coordinate_y = pyo.Param(
        model.zones, initialize=coordinate_y_data, within=pyo.Reals
    )

    model.x = pyo.Var(
        model.departments, model.zones, domain=pyo.Binary
    )
    model.y = pyo.Var(
        model.department_pairs, model.zone_arcs, domain=pyo.UnitInterval
    )

    def department_assignment_rule(mdl, department):
        return sum(mdl.x[department, zone] for zone in mdl.zones) == 1

    model.department_assignment = pyo.Constraint(
        model.departments, rule=department_assignment_rule
    )

    def zone_assignment_rule(mdl, zone):
        return sum(
            mdl.x[department, zone] for department in mdl.departments
        ) == 1

    model.zone_assignment = pyo.Constraint(
        model.zones, rule=zone_assignment_rule
    )

    # Binary assignments and these two marginal equalities force y to
    # represent the unique ordered zone pair occupied by each department pair.
    def first_marginal_rule(mdl, first, second, origin):
        return sum(
            mdl.y[first, second, origin, destination]
            for destination in mdl.zones
            if destination != origin
        ) == mdl.x[first, origin]

    model.first_marginal = pyo.Constraint(
        model.department_pairs, model.zones, rule=first_marginal_rule
    )

    def second_marginal_rule(mdl, first, second, destination):
        return sum(
            mdl.y[first, second, origin, destination]
            for origin in mdl.zones
            if origin != destination
        ) == mdl.x[second, destination]

    model.second_marginal = pyo.Constraint(
        model.department_pairs, model.zones, rule=second_marginal_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.flow[first, second]
            * model.distance[min(origin, destination), max(origin, destination)]
            * model.y[first, second, origin, destination]
            for first, second in model.department_pairs
            for origin, destination in model.zone_arcs
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        # HiGHS can raise when no feasible solution can be loaded.
        # Success is still determined solely by objective retrieval below.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}