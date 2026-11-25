# IR: {"sets":{"V":[0,1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","R":[[0,1],[1,3],[2,6],[3,4],[3,5],[3,6],[5,6]]},"params":{"distance_matrix":"params['distance_matrix']; 49 nonnegative distances, flattened row-major","d[i,j]":"distance_matrix[7*i+j]"},"variables":{"x[i,j]":"nonnegative integer traversal count for (i,j) in A"},"constraints":{"coverage":"x[i,j]+x[j,i] >= 1 for (i,j) in R","balance":"sum(x[i,j] for j != i) == sum(x[j,i] for j != i) for i in V"},"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)","connectivity":"R is connected and spans V; coverage and balance therefore yield an Euler circuit starting and ending at depot 0"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = params["distance_matrix"]
    if len(distances) != 49:
        raise ValueError("distance_matrix must contain exactly 49 entries.")

    model = pyo.ConcreteModel()

    model.vertices = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
    )
    model.required_edges = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1),
            (1, 3),
            (2, 6),
            (3, 4),
            (3, 5),
            (3, 6),
            (5, 6),
        ],
    )

    model.distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): distances[7 * i + j]
            for i, j in model.arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.traversals = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(current_model, i, j):
        return (
            current_model.traversals[i, j]
            + current_model.traversals[j, i]
            >= 1
        )

    model.required_coverage = pyo.Constraint(
        model.required_edges,
        rule=coverage_rule,
    )

    def balance_rule(current_model, i):
        return (
            sum(
                current_model.traversals[i, j]
                for j in current_model.vertices
                if j != i
            )
            == sum(
                current_model.traversals[j, i]
                for j in current_model.vertices
                if j != i
            )
        )

    model.flow_balance = pyo.Constraint(
        model.vertices,
        rule=balance_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.traversals[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # The required edges connect every vertex, including depot 0.
    # Their coverage makes the balanced traversal multigraph connected,
    # so its traversals form a single closed Euler circuit.

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}