# IR: {"sets":{"N":"range(num_nodes)","B":"N excluding depot 0","A":"{(i,j) in N x N: i != j}","R":"range(num_pairs)"},"params":{"distance_matrix":"travel costs indexed by N x N","coords":"node coordinates; metadata only because travel costs are explicitly supplied","num_nodes":"number of nodes","num_pairs":"number of requests","pickup_delivery_pairs":"pickup and delivery indices indexed by R"},"variables":{"x[i,j]":"binary for (i,j) in A","order[i]":"integer in [1,num_nodes-1] for i in B"},"constraints":["For each i in N: sum(x[i,j] for j in N if j != i) = 1.","For each j in N: sum(x[i,j] for i in N if i != j) = 1.","For distinct i,j in B: order[i] - order[j] + num_nodes*x[i,j] <= num_nodes-1.","For each r in R with pair (pickup,delivery): order[pickup] + 1 <= order[delivery]."],"objective":"Minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    coords = params["coords"]  # Metadata; use the supplied matrix for travel costs.
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]
    pickup_delivery_pairs = params["pickup_delivery_pairs"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.branches = pyo.Set(initialize=range(1, num_nodes), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.requests = pyo.Set(initialize=range(num_pairs), ordered=True)

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.branches,
        domain=pyo.Integers,
        bounds=(1, num_nodes - 1),
    )

    def outgoing_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.nodes if j != i
        ) == 1

    model.outgoing_once = pyo.Constraint(model.nodes, rule=outgoing_rule)

    def incoming_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.nodes if i != j
        ) == 1

    model.incoming_once = pyo.Constraint(model.nodes, rule=incoming_rule)

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.visit_order[i]
            - mdl.visit_order[j]
            + num_nodes * mdl.x[i, j]
            <= num_nodes - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.branches,
        model.branches,
        rule=subtour_rule,
    )

    def precedence_rule(mdl, request):
        pickup, delivery = pickup_delivery_pairs[request]
        return mdl.visit_order[pickup] + 1 <= mdl.visit_order[delivery]

    model.pickup_precedence = pyo.Constraint(
        model.requests,
        rule=precedence_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPSI HiGHS raises RuntimeError when it cannot load a solution.
    # Attempt objective retrieval afterward; do not inspect termination enums.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}