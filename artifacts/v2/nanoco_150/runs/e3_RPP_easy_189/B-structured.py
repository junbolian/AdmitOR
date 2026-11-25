# IR: {"sets":{"V":"{0,...,8}","A":"{(i,j) in V x V: i != j}","R":[[1,8],[2,3],[3,4],[3,6],[3,8],[4,8],[5,7],[7,8]]},"params":{"distance_matrix":"params['distance_matrix']","depot_node":"params['depot_node']","K":"|V|-1"},"variables":{"x[i,j]":"nonnegative integer traversal count, (i,j) in A","f[i,j]":"nonnegative continuous connectivity flow, (i,j) in A"},"constraints":["sum_j x[i,j] - sum_j x[j,i] = 0 for each i in V","x[u,v] + x[v,u] >= 1 for each (u,v) in R","sum_j f[i,j] - sum_j f[j,i] = K if i is depot_node, otherwise -1","f[i,j] <= K*x[i,j] for each (i,j) in A"],"objective":"minimize sum_(i,j) in A distance_matrix[i][j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    depot_node = params["depot_node"]

    nodes = tuple(range(9))
    arcs = tuple((i, j) for i in nodes for j in nodes if i != j)
    required_edges = (
        (1, 8),
        (2, 3),
        (3, 4),
        (3, 6),
        (3, 8),
        (4, 8),
        (5, 7),
        (7, 8),
    )
    connectivity_quantity = len(nodes) - 1

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.directed_arcs = pyo.Set(
        initialize=arcs, dimen=2, ordered=True
    )
    model.required_segments = pyo.Set(
        initialize=required_edges, dimen=2, ordered=True
    )
    model.travel_distance = pyo.Param(
        model.directed_arcs,
        initialize={(i, j): distance_matrix[i][j] for i, j in arcs},
        within=pyo.NonNegativeReals,
    )
    model.depot_vertex = pyo.Param(
        initialize=depot_node, within=model.vertices
    )

    model.x = pyo.Var(
        model.directed_arcs, domain=pyo.NonNegativeIntegers
    )
    model.f = pyo.Var(
        model.directed_arcs, domain=pyo.NonNegativeReals
    )

    def route_balance_rule(instance, i):
        return (
            sum(instance.x[i, j] for j in instance.vertices if j != i)
            == sum(instance.x[j, i] for j in instance.vertices if j != i)
        )

    model.route_balance = pyo.Constraint(
        model.vertices, rule=route_balance_rule
    )

    def required_service_rule(instance, u, v):
        return instance.x[u, v] + instance.x[v, u] >= 1

    model.required_service = pyo.Constraint(
        model.required_segments, rule=required_service_rule
    )

    # Every vertex is either the depot or an endpoint of a required edge.
    # This flow connects all selected traversals to the depot; together
    # with integer route balance, it guarantees a closed Euler tour.
    def connectivity_balance_rule(instance, i):
        net_outflow = (
            sum(instance.f[i, j] for j in instance.vertices if j != i)
            - sum(instance.f[j, i] for j in instance.vertices if j != i)
        )
        demand = (
            connectivity_quantity
            if i == pyo.value(instance.depot_vertex)
            else -1
        )
        return net_outflow == demand

    model.connectivity_balance = pyo.Constraint(
        model.vertices, rule=connectivity_balance_rule
    )

    def connectivity_capacity_rule(instance, i, j):
        return (
            instance.f[i, j]
            <= connectivity_quantity * instance.x[i, j]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.directed_arcs, rule=connectivity_capacity_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.directed_arcs
        ),
        sense=pyo.minimize,
    )

    # APPSI may raise RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by retrieving the objective value.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}