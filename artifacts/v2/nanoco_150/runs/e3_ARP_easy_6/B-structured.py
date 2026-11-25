# IR: {"sets":{"N":"0..n-1","A":"{(i,j) in N*N: i!=j}","R":"required_segments"},"params":{"n":"params['num_junctions']","r":"params['num_required_segments']","depot":"params['depot_junction']","d":"params['distance_matrix']","coord_x":"params['junction_coords_x']","coord_y":"params['junction_coords_y']","B":"n*(r+1)+r"},"variables":{"x[i,j]":"integer, 0<=x<=B; traversal counts","visit[i]":"binary; visited junctions","flow[i,j]":"continuous, nonnegative; depot connectivity flow"},"constraints":["visit[depot]=1","x[i,j]<=B*visit[i] for (i,j) in A","x[i,j]<=B*visit[j] for (i,j) in A","sum_j x[i,j]=sum_j x[j,i] for i in N","x[u,v]+x[v,u]>=1 for (u,v) in R","flow[i,j]<=(n-1)*x[i,j] for (i,j) in A","sum_j flow[j,i]-sum_j flow[i,j]=visit[i] for i!=depot","sum_j flow[depot,j]-sum_j flow[j,depot]=sum_{i!=depot} visit[i]"],"objective":"minimize sum_{(i,j) in A} d[i,j]*x[i,j]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_raw = params["num_junctions"]
    r_raw = params["num_required_segments"]
    depot_raw = params["depot_junction"]
    distance_matrix = params["distance_matrix"]
    junction_coords_x = params["junction_coords_x"]
    junction_coords_y = params["junction_coords_y"]
    required_segments_raw = params["required_segments"]

    n = int(n_raw)
    r = int(r_raw)
    depot = int(depot_raw)

    if (
        n != n_raw
        or r != r_raw
        or depot != depot_raw
        or n < 1
        or r < 0
        or not 0 <= depot < n
    ):
        return {"objective": None, "status": "invalid_parameters"}

    if (
        len(distance_matrix) != n
        or any(len(row) != n for row in distance_matrix)
        or len(junction_coords_x) != n
        or len(junction_coords_y) != n
        or len(required_segments_raw) != r
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    required_segments = []
    for segment in required_segments_raw:
        if len(segment) != 2:
            return {"objective": None, "status": "invalid_required_segment"}
        first_raw, second_raw = segment
        first = int(first_raw)
        second = int(second_raw)
        if (
            first != first_raw
            or second != second_raw
            or not 0 <= first < n
            or not 0 <= second < n
            or first == second
        ):
            return {"objective": None, "status": "invalid_required_segment"}
        required_segments.append((first, second))

    distances = {
        (first, second): float(distance_matrix[first][second])
        for first in range(n)
        for second in range(n)
    }
    coordinates_x = {
        junction: float(junction_coords_x[junction]) for junction in range(n)
    }
    coordinates_y = {
        junction: float(junction_coords_y[junction]) for junction in range(n)
    }

    if any(
        not math.isfinite(distance) or distance < 0
        for distance in distances.values()
    ):
        return {"objective": None, "status": "invalid_distances"}

    if any(
        not math.isfinite(coordinate)
        for coordinate in (
            list(coordinates_x.values()) + list(coordinates_y.values())
        )
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    # With nonnegative costs, connector walks between required services can
    # be simplified to simple paths. Thus an optimal circuit exists within
    # this total-traversal bound, which also bounds each individual arc.
    traversal_bound = n * (r + 1) + r

    model = pyo.ConcreteModel()
    model.junctions = pyo.Set(initialize=range(n), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (first, second)
            for first in range(n)
            for second in range(n)
            if first != second
        ],
        ordered=True,
    )
    model.required_ids = pyo.Set(initialize=range(r), ordered=True)

    # Coordinates are retained as input data; the supplied matrix determines
    # travel costs, so distances are not recomputed from coordinates.
    model.distance = pyo.Param(
        model.junctions, model.junctions, initialize=distances
    )
    model.coord_x = pyo.Param(model.junctions, initialize=coordinates_x)
    model.coord_y = pyo.Param(model.junctions, initialize=coordinates_y)

    model.x = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, traversal_bound),
    )
    model.visit = pyo.Var(model.junctions, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.depot_visited = pyo.Constraint(expr=model.visit[depot] == 1)

    def tail_visit_rule(problem, first, second):
        return problem.x[first, second] <= traversal_bound * problem.visit[first]

    def head_visit_rule(problem, first, second):
        return problem.x[first, second] <= traversal_bound * problem.visit[second]

    model.tail_visit = pyo.Constraint(model.arcs, rule=tail_visit_rule)
    model.head_visit = pyo.Constraint(model.arcs, rule=head_visit_rule)

    def vehicle_balance_rule(problem, junction):
        if n == 1:
            return pyo.Constraint.Feasible
        return (
            pyo.quicksum(
                problem.x[junction, other]
                for other in problem.junctions
                if other != junction
            )
            == pyo.quicksum(
                problem.x[other, junction]
                for other in problem.junctions
                if other != junction
            )
        )

    model.vehicle_balance = pyo.Constraint(
        model.junctions, rule=vehicle_balance_rule
    )

    def service_rule(problem, required_id):
        first, second = required_segments[required_id]
        return problem.x[first, second] + problem.x[second, first] >= 1

    model.required_service = pyo.Constraint(
        model.required_ids, rule=service_rule
    )

    def flow_capacity_rule(problem, first, second):
        return problem.flow[first, second] <= (n - 1) * problem.x[first, second]

    model.flow_capacity = pyo.Constraint(model.arcs, rule=flow_capacity_rule)

    def connectivity_balance_rule(problem, junction):
        if n == 1:
            return pyo.Constraint.Feasible

        incoming = pyo.quicksum(
            problem.flow[other, junction]
            for other in problem.junctions
            if other != junction
        )
        outgoing = pyo.quicksum(
            problem.flow[junction, other]
            for other in problem.junctions
            if other != junction
        )

        if junction == depot:
            return outgoing - incoming == pyo.quicksum(
                problem.visit[other]
                for other in problem.junctions
                if other != depot
            )
        return incoming - outgoing == problem.visit[junction]

    model.connectivity_balance = pyo.Constraint(
        model.junctions, rule=connectivity_balance_rule
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.distance[first, second] * model.x[first, second]
            for first, second in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this specific error when it cannot load a solution.
        # Other runtime errors are unexpected and propagate.
        if "A feasible solution was not found" in str(error):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}