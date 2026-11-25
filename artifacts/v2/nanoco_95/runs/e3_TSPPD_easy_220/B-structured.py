# IR: {"sets":{"N":[0,1,2,3,4,5,6],"B":[1,2,3,4,5,6],"A":"{(i,j) in N x N: i != j}","K":[0,1],"P":[[4,3],[2,6],[5,1]]},"params":{"coords":"params['coords']; node coordinates, metadata only","distance_matrix":"params['distance_matrix']; authoritative travel distances"},"variables":{"x[i,j]":"binary for (i,j) in A","position[i]":"continuous in [1,6] for i in B"},"constraints":["For each i in N: sum(x[i,j] for j != i) = 1.","For each j in N: sum(x[i,j] for i != j) = 1.","For distinct i,j in B: position[i] - position[j] + 6*x[i,j] <= 5.","For each (pickup,delivery) in P: position[pickup] + 1 <= position[delivery]."],"objective":"Minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    num_nodes = 7
    num_branches = num_nodes - 1
    pickup_delivery_pairs = [(4, 3), (2, 6), (5, 1)]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.branches = pyo.RangeSet(1, num_nodes - 1)
    model.axes = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ],
    )
    model.requests = pyo.Set(
        dimen=2,
        initialize=pickup_delivery_pairs,
    )

    model.coordinates = pyo.Param(
        model.nodes,
        model.axes,
        initialize=lambda instance, i, axis: coords[i][axis],
        within=pyo.Reals,
    )
    model.travel_distance = pyo.Param(
        model.arcs,
        initialize=lambda instance, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.branches,
        domain=pyo.Reals,
        bounds=(1, num_branches),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.nodes if j != i
        ) == 1

    model.outgoing = pyo.Constraint(model.nodes, rule=outgoing_rule)

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.nodes if i != j
        ) == 1

    model.incoming = pyo.Constraint(model.nodes, rule=incoming_rule)

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.position[i]
            - instance.position[j]
            + num_branches * instance.x[i, j]
            <= num_branches - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.branches,
        model.branches,
        rule=subtour_rule,
    )

    def precedence_rule(instance, pickup, delivery):
        return instance.position[pickup] + 1 <= instance.position[delivery]

    model.pickup_precedence = pyo.Constraint(
        model.requests,
        rule=precedence_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when it cannot load a feasible solution.
        # Success is still determined solely by objective retrieval below.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solver_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}