# IR: {"sets":{"N":"range(num_nodes)","B":"N excluding depot 0","A":"(i,j) in N x N with i != j","R":"range(num_pairs)","K":[0,1]},"params":{"num_nodes":"params['num_nodes']","num_pairs":"params['num_pairs']","distance_matrix":"params['distance_matrix']","coords":"params['coords'] (metadata; distances govern cost)","pickup_delivery_pairs":"params['pickup_delivery_pairs']"},"variables":{"x[i,j]":"binary for (i,j) in A","order[i]":"continuous in [1,num_nodes-1] for i in B"},"constraints":["outgoing[i]: sum(x[i,j] for j != i) = 1 for i in N","incoming[j]: sum(x[i,j] for i != j) = 1 for j in N","subtour[i,j]: order[i]-order[j]+(num_nodes-1)*x[i,j] <= num_nodes-2 for distinct i,j in B","precedence[r]: order[pickup[r]]+1 <= order[delivery[r]] for r in R"],"objective":"minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_pairs = int(params["num_pairs"])
    distance_matrix = params["distance_matrix"]
    coords = params["coords"]
    pickup_delivery_pairs = params["pickup_delivery_pairs"]

    if num_nodes < 2 or num_pairs < 0:
        raise ValueError("Invalid node or request count.")
    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        raise ValueError("distance_matrix must have num_nodes rows and columns.")
    if len(coords) != num_nodes or any(len(point) != 2 for point in coords):
        raise ValueError("coords must contain one coordinate pair per node.")
    if len(pickup_delivery_pairs) != num_pairs:
        raise ValueError("pickup_delivery_pairs must contain num_pairs requests.")

    for pair in pickup_delivery_pairs:
        if len(pair) != 2:
            raise ValueError("Each request must contain a pickup and delivery node.")
        pickup, delivery = pair
        if (
            pickup not in range(1, num_nodes)
            or delivery not in range(1, num_nodes)
            or pickup == delivery
        ):
            raise ValueError("Requests must reference distinct branch nodes.")

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.branches = pyo.Set(initialize=range(1, num_nodes), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ],
    )
    model.requests = pyo.Set(initialize=range(num_pairs), ordered=True)
    model.coordinate_axes = pyo.Set(initialize=[0, 1], ordered=True)

    model.distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in range(num_nodes)
            for j in range(num_nodes)
        },
        within=pyo.NonNegativeReals,
    )
    model.coordinate = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize={
            (i, axis): coords[i][axis]
            for i in range(num_nodes)
            for axis in range(2)
        },
        within=pyo.Reals,
    )
    model.pickup_node = pyo.Param(
        model.requests,
        initialize={
            r: pickup_delivery_pairs[r][0] for r in range(num_pairs)
        },
        within=model.branches,
    )
    model.delivery_node = pyo.Param(
        model.requests,
        initialize={
            r: pickup_delivery_pairs[r][1] for r in range(num_pairs)
        },
        within=model.branches,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.order = pyo.Var(
        model.branches,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def outgoing_rule(model, i):
        return sum(model.x[i, j] for j in model.nodes if j != i) == 1

    model.outgoing = pyo.Constraint(model.nodes, rule=outgoing_rule)

    def incoming_rule(model, j):
        return sum(model.x[i, j] for i in model.nodes if i != j) == 1

    model.incoming = pyo.Constraint(model.nodes, rule=incoming_rule)

    def subtour_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            model.order[i]
            - model.order[j]
            + (num_nodes - 1) * model.x[i, j]
            <= num_nodes - 2
        )

    model.subtour = pyo.Constraint(
        model.branches,
        model.branches,
        rule=subtour_rule,
    )

    def precedence_rule(model, r):
        pickup = pyo.value(model.pickup_node[r])
        delivery = pyo.value(model.delivery_node[r])
        return model.order[pickup] + 1 <= model.order[delivery]

    model.precedence = pyo.Constraint(
        model.requests,
        rule=precedence_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}