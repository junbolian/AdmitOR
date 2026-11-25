# {
#   "sets": {"D": [0,1,2,3], "Z": [0,1,2,3], "P": "[(i,j) in D x D: i<j]", "A": "[(k,l) in Z x Z: k!=l]"},
#   "params": {
#     "flow": ["flow_01","flow_02","flow_03","flow_12","flow_13","flow_23"],
#     "distance": ["dist_01","dist_02","dist_03","dist_12","dist_13","dist_23"],
#     "coordinates": ["coord_x0","coord_y0","coord_x1","coord_y1","coord_x2","coord_y2","coord_x3","coord_y3"],
#     "interpretation": "Flows are indexed by P; distances are symmetric on A; coordinates are metadata; supplied integer distances determine costs."
#   },
#   "variables": {"x[i,k]": "Binary for i in D, k in Z", "y[i,j,k,l]": "Continuous in [0,1] for (i,j) in P, (k,l) in A"},
#   "constraints": [
#     "sum(k in Z) x[i,k] = 1 for each i in D",
#     "sum(i in D) x[i,k] = 1 for each k in Z",
#     "y[i,j,k,l] <= x[i,k] for each (i,j) in P, (k,l) in A",
#     "y[i,j,k,l] <= x[j,l] for each (i,j) in P, (k,l) in A",
#     "y[i,j,k,l] >= x[i,k] + x[j,l] - 1 for each (i,j) in P, (k,l) in A"
#   ],
#   "objective": "Minimize sum((i,j) in P, (k,l) in A) flow[i,j] * distance[k,l] * y[i,j,k,l]; count each unordered department pair once."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flows = {
        (0, 1): params["flow_01"],
        (0, 2): params["flow_02"],
        (0, 3): params["flow_03"],
        (1, 2): params["flow_12"],
        (1, 3): params["flow_13"],
        (2, 3): params["flow_23"],
    }
    unordered_distances = {
        (0, 1): params["dist_01"],
        (0, 2): params["dist_02"],
        (0, 3): params["dist_03"],
        (1, 2): params["dist_12"],
        (1, 3): params["dist_13"],
        (2, 3): params["dist_23"],
    }
    coordinates_x = {
        0: params["coord_x0"],
        1: params["coord_x1"],
        2: params["coord_x2"],
        3: params["coord_x3"],
    }
    coordinates_y = {
        0: params["coord_y0"],
        1: params["coord_y1"],
        2: params["coord_y2"],
        3: params["coord_y3"],
    }

    model = pyo.ConcreteModel()
    model.departments = pyo.RangeSet(0, 3)
    model.zones = pyo.RangeSet(0, 3)
    model.department_pairs = pyo.Set(
        dimen=2,
        initialize=flows.keys(),
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

    distances = {
        (origin, destination): unordered_distances[
            (min(origin, destination), max(origin, destination))
        ]
        for origin, destination in model.zone_arcs
    }

    model.flow = pyo.Param(
        model.department_pairs,
        initialize=flows,
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.zone_arcs,
        initialize=distances,
        within=pyo.Reals,
    )
    model.coord_x = pyo.Param(
        model.zones,
        initialize=coordinates_x,
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.zones,
        initialize=coordinates_y,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.departments,
        model.zones,
        domain=pyo.Binary,
    )
    model.y = pyo.Var(
        model.department_pairs,
        model.zone_arcs,
        domain=pyo.UnitInterval,
    )

    def department_assignment_rule(instance, department):
        return sum(
            instance.x[department, zone] for zone in instance.zones
        ) == 1

    model.department_assignment = pyo.Constraint(
        model.departments,
        rule=department_assignment_rule,
    )

    def zone_assignment_rule(instance, zone):
        return sum(
            instance.x[department, zone]
            for department in instance.departments
        ) == 1

    model.zone_assignment = pyo.Constraint(
        model.zones,
        rule=zone_assignment_rule,
    )

    def pair_upper_first_rule(instance, first, second, origin, destination):
        return (
            instance.y[first, second, origin, destination]
            <= instance.x[first, origin]
        )

    def pair_upper_second_rule(instance, first, second, origin, destination):
        return (
            instance.y[first, second, origin, destination]
            <= instance.x[second, destination]
        )

    def pair_lower_rule(instance, first, second, origin, destination):
        return (
            instance.y[first, second, origin, destination]
            >= instance.x[first, origin]
            + instance.x[second, destination]
            - 1
        )

    model.pair_upper_first = pyo.Constraint(
        model.department_pairs,
        model.zone_arcs,
        rule=pair_upper_first_rule,
    )
    model.pair_upper_second = pyo.Constraint(
        model.department_pairs,
        model.zone_arcs,
        rule=pair_upper_second_rule,
    )
    model.pair_lower = pyo.Constraint(
        model.department_pairs,
        model.zone_arcs,
        rule=pair_lower_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.flow[first, second]
            * model.distance[origin, destination]
            * model.y[first, second, origin, destination]
            for first, second in model.department_pairs
            for origin, destination in model.zone_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}