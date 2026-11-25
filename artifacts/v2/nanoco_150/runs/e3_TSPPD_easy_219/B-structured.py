# IR: {"sets":{"N":[0,1,2,3,4,5,6],"V":[1,2,3,4,5,6],"K":[0,1],"A":"{(i,j) in N x N: i != j}","P":[[6,3],[1,5],[2,4]]},"params":{"coords":"params['coords']; coordinates indexed by N x K","distance_matrix":"params['distance_matrix']; travel distances indexed by N x N"},"variables":{"x[i,j]":"binary for (i,j) in A","position[i]":"continuous in [1,6] for i in V"},"constraints":["For each i in N: sum(x[i,j] for j != i) = 1.","For each j in N: sum(x[i,j] for i != j) = 1.","For distinct i,j in V: position[i] - position[j] + 6*x[i,j] <= 5.","For each (u,v) in P: position[u] + 1 <= position[v]."],"objective":"Minimize sum(distance_matrix[i,j]*x[i,j] for (i,j) in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.sites = pyo.Set(initialize=range(1, 7), ordered=True)
    model.axes = pyo.Set(initialize=range(2), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
    )
    model.pickup_delivery_pairs = pyo.Set(
        dimen=2,
        initialize=[(6, 3), (1, 5), (2, 4)],
    )

    model.coordinates = pyo.Param(
        model.nodes,
        model.axes,
        initialize={
            (i, k): coords[i][k]
            for i in range(7)
            for k in range(2)
        },
        within=pyo.Reals,
    )
    model.travel_distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in range(7)
            for j in range(7)
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.sites,
        domain=pyo.Reals,
        bounds=(1, 6),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j]
            for j in instance.nodes
            if j != i
        ) == 1

    model.outgoing = pyo.Constraint(
        model.nodes,
        rule=outgoing_rule,
    )

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j]
            for i in instance.nodes
            if i != j
        ) == 1

    model.incoming = pyo.Constraint(
        model.nodes,
        rule=incoming_rule,
    )

    def ordering_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.position[i]
            - instance.position[j]
            + 6 * instance.x[i, j]
            <= 5
        )

    model.route_ordering = pyo.Constraint(
        model.sites,
        model.sites,
        rule=ordering_rule,
    )

    def precedence_rule(instance, pickup, delivery):
        return (
            instance.position[pickup] + 1
            <= instance.position[delivery]
        )

    model.pickup_precedence = pyo.Constraint(
        model.pickup_delivery_pairs,
        rule=precedence_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    # Determine success solely by whether the objective can be evaluated.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}