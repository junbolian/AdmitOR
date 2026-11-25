# IR: {"sets":{"V":"0..n-1","C":"V excluding depot 0","A":"(i,j) in V x V with i != j","R":"0..r-1"},"params":{"n":"params[num_nodes], required to equal 7","r":"params[num_requisitions], required to equal 3","d":"params[distance_matrix]","coordinates":"params[depot_x], params[depot_y], and params[nodek_x], params[nodek_y] for k=1..6; metadata only","pairs":"[(4,6),(5,1),(2,3)] indexed by R"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [1,n-1] for i in C"},"constraints":["outgoing: sum(x[i,j] for j in V if j != i) = 1 for i in V","incoming: sum(x[i,j] for i in V if i != j) = 1 for j in V","subtour: u[i]-u[j]+(n-1)*x[i,j] <= n-2 for distinct i,j in C","precedence: u[pickup[k]]+1 <= u[delivery[k]] for k in R"],"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_input = params["num_nodes"]
    r_input = params["num_requisitions"]
    distance_matrix = params["distance_matrix"]

    coordinates = {
        0: (params["depot_x"], params["depot_y"]),
        1: (params["node1_x"], params["node1_y"]),
        2: (params["node2_x"], params["node2_y"]),
        3: (params["node3_x"], params["node3_y"]),
        4: (params["node4_x"], params["node4_y"]),
        5: (params["node5_x"], params["node5_y"]),
        6: (params["node6_x"], params["node6_y"]),
    }
    pairs = ((4, 6), (5, 1), (2, 3))

    if n_input != len(coordinates) or r_input != len(pairs):
        return {"objective": None, "status": "invalid_dimensions"}

    n = int(n_input)
    r = int(r_input)

    if len(distance_matrix) != n or any(
        len(row) != n for row in distance_matrix
    ):
        return {"objective": None, "status": "invalid_distance_matrix"}

    model = pyo.ConcreteModel()

    model.locations = pyo.Set(initialize=range(n), ordered=True)
    model.customers = pyo.Set(initialize=range(1, n), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(n)
            for j in range(n)
            if i != j
        ),
    )
    model.requisitions = pyo.Set(initialize=range(r), ordered=True)

    model.travel_distance = pyo.Param(
        model.arcs,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )
    model.x_coordinate = pyo.Param(
        model.locations,
        initialize={i: coordinates[i][0] for i in range(n)},
        within=pyo.Reals,
    )
    model.y_coordinate = pyo.Param(
        model.locations,
        initialize={i: coordinates[i][1] for i in range(n)},
        within=pyo.Reals,
    )
    model.pickup_node = pyo.Param(
        model.requisitions,
        initialize={k: pairs[k][0] for k in range(r)},
        within=model.customers,
    )
    model.delivery_node = pyo.Param(
        model.requisitions,
        initialize={k: pairs[k][1] for k in range(r)},
        within=model.customers,
    )

    model.use_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.customers,
        domain=pyo.Integers,
        bounds=(1, n - 1),
    )

    def outgoing_rule(mdl, i):
        return sum(
            mdl.use_arc[i, j] for j in mdl.locations if j != i
        ) == 1

    model.outgoing_visit = pyo.Constraint(
        model.locations, rule=outgoing_rule
    )

    def incoming_rule(mdl, j):
        return sum(
            mdl.use_arc[i, j] for i in mdl.locations if i != j
        ) == 1

    model.incoming_visit = pyo.Constraint(
        model.locations, rule=incoming_rule
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.visit_order[i]
            - mdl.visit_order[j]
            + (n - 1) * mdl.use_arc[i, j]
            <= n - 2
        )

    model.subtour_elimination = pyo.Constraint(
        model.customers,
        model.customers,
        rule=subtour_rule,
    )

    def precedence_rule(mdl, k):
        pickup = int(pyo.value(mdl.pickup_node[k]))
        delivery = int(pyo.value(mdl.delivery_node[k]))
        return mdl.visit_order[pickup] + 1 <= mdl.visit_order[delivery]

    model.pickup_precedence = pyo.Constraint(
        model.requisitions, rule=precedence_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.use_arc[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}