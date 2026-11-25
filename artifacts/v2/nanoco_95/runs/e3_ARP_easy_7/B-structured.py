# IR: {"sets":{"V":"range(num_intersections), depot=0","A":"{(i,j) in V x V: i!=j}","K":"range(num_required_segments)","R":"nondepot endpoints of required_segment_relations"},"params":{"depot_coordinates":"input metadata","intersection_coordinates":"input metadata","distance_matrix":"nonnegative arc costs d[i,j]","required_segment_relations":"required undirected endpoint pairs (u[k],v[k])","num_required_segments":"required-list size","num_intersections":"node-set size","num_trucks":"available trucks; frozen at one","B":"|R|","demand[i]":"1 if i in R, otherwise 0"},"variables":{"x[i,j]":"nonnegative integer traversal count","f[i,j]":"nonnegative continuous connectivity flow"},"constraints":["For each k: x[u[k],v[k]]+x[v[k],u[k]]>=1.","For each i: sum_j x[i,j]=sum_j x[j,i].","At depot: sum_j f[0,j]-sum_j f[j,0]=B.","For each i!=0: sum_j f[j,i]-sum_j f[i,j]=demand[i].","For each (i,j): f[i,j]<=B*x[i,j]."],"objective":"minimize sum_(i,j) d[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    depot_coordinates = params["depot_coordinates"]
    intersection_coordinates = params["intersection_coordinates"]
    distance_matrix = params["distance_matrix"]
    required_segment_relations = params["required_segment_relations"]
    num_required_segments = params["num_required_segments"]
    num_intersections = params["num_intersections"]
    num_trucks = params["num_trucks"]

    # Coordinates are descriptive metadata; the supplied matrix defines costs.
    _ = depot_coordinates, intersection_coordinates

    if (
        num_intersections != int(num_intersections)
        or num_intersections < 2
        or num_required_segments != int(num_required_segments)
        or num_required_segments < 0
    ):
        return {"objective": None, "status": "invalid_set_sizes"}

    # This formulation implements the specified, fixed single-truck problem.
    if num_trucks != 1:
        return {"objective": None, "status": "requires_one_truck"}

    node_count = int(num_intersections)
    required_count = int(num_required_segments)
    vertices = list(range(node_count))

    if len(required_segment_relations) != required_count:
        return {"objective": None, "status": "invalid_required_count"}

    if len(distance_matrix) != node_count or any(
        len(row) != node_count for row in distance_matrix
    ):
        return {"objective": None, "status": "invalid_distance_matrix"}

    required_edges = []
    for endpoints in required_segment_relations:
        if len(endpoints) != 2:
            return {"objective": None, "status": "invalid_required_segment"}
        first, second = endpoints
        if first not in vertices or second not in vertices or first == second:
            return {"objective": None, "status": "invalid_required_segment"}
        required_edges.append((int(first), int(second)))

    arcs = [
        (first, second)
        for first in vertices
        for second in vertices
        if first != second
    ]
    required_vertices = {
        vertex
        for endpoints in required_edges
        for vertex in endpoints
        if vertex != 0
    }
    connectivity_demand = len(required_vertices)

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vertices, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.K = pyo.Set(initialize=range(required_count), ordered=True)
    model.R = pyo.Set(initialize=sorted(required_vertices), within=model.V)

    model.travel_cost = pyo.Param(
        model.A,
        initialize={
            (first, second): distance_matrix[first][second]
            for first, second in arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.flow_amount = pyo.Param(
        initialize=connectivity_demand,
        within=pyo.NonNegativeIntegers,
    )
    model.node_demand = pyo.Param(
        model.V,
        initialize={
            vertex: int(vertex in required_vertices) for vertex in vertices
        },
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def coverage_rule(current, segment):
        first, second = required_edges[segment]
        return current.x[first, second] + current.x[second, first] >= 1

    model.required_coverage = pyo.Constraint(model.K, rule=coverage_rule)

    def balance_rule(current, vertex):
        return (
            pyo.quicksum(
                current.x[vertex, other]
                for other in current.V
                if other != vertex
            )
            == pyo.quicksum(
                current.x[other, vertex]
                for other in current.V
                if other != vertex
            )
        )

    model.traversal_balance = pyo.Constraint(model.V, rule=balance_rule)

    def connectivity_rule(current, vertex):
        outbound = pyo.quicksum(
            current.f[vertex, other]
            for other in current.V
            if other != vertex
        )
        inbound = pyo.quicksum(
            current.f[other, vertex]
            for other in current.V
            if other != vertex
        )
        if vertex == 0:
            return outbound - inbound == current.flow_amount
        return inbound - outbound == current.node_demand[vertex]

    model.connectivity_balance = pyo.Constraint(
        model.V, rule=connectivity_rule
    )

    def flow_capacity_rule(current, first, second):
        return (
            current.f[first, second]
            <= current.flow_amount * current.x[first, second]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.A, rule=flow_capacity_rule
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.travel_cost[first, second] * model.x[first, second]
            for first, second in model.A
        ),
        sense=pyo.minimize,
    )

    # Catch only expected solver failures; unexpected errors propagate.
    failure_reason = None
    try:
        Highs().solve(model)
    except ApplicationError:
        failure_reason = "solver_failed"
    except RuntimeError as error:
        if "feasible solution was not found" not in str(error).lower():
            raise
        failure_reason = "no_feasible_solution"

    # Success is determined solely by objective-value retrieval.
    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": failure_reason or "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}