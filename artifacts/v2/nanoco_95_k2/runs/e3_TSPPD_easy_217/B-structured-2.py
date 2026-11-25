# IR: {"sets":{"V":"range(num_nodes)","C":"V excluding 0","A":"[(i,j) in V x V: i != j]","P":[[4,5],[6,1],[2,3]]},"params":{"distance_matrix":"fuel costs indexed by V x V","num_nodes":"frozen node count: 7","num_pairs":"frozen pair count: 3"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"real in [1,num_nodes-1] for i in C"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1.","For each j in V: sum(x[i,j] for i != j) = 1.","For distinct i,j in C: u[i]-u[j]+(num_nodes-1)*x[i,j] <= num_nodes-2.","For each (pickup,delivery) in P: u[pickup]+1 <= u[delivery]."],"objective":"Minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]

    pickup_delivery_pairs = ((4, 5), (6, 1), (2, 3))

    if num_nodes != 7 or num_pairs != len(pickup_delivery_pairs):
        raise ValueError("The node and pair counts must match the frozen instance.")

    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        raise ValueError("distance_matrix must have shape num_nodes by num_nodes.")

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.customers = pyo.Set(initialize=range(1, num_nodes), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.task_pairs = pyo.Set(
        dimen=2,
        initialize=pickup_delivery_pairs,
    )

    model.fuel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.nodes if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.nodes,
        rule=departure_rule,
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.nodes if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.nodes,
        rule=arrival_rule,
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i]
            - instance.u[j]
            + (num_nodes - 1) * instance.x[i, j]
            <= num_nodes - 2
        )

    model.subtour_constraints = pyo.Constraint(
        model.customers,
        model.customers,
        rule=subtour_rule,
    )

    def precedence_rule(instance, pickup, delivery):
        return instance.u[pickup] + 1 <= instance.u[delivery]

    model.precedence_constraints = pyo.Constraint(
        model.task_pairs,
        rule=precedence_rule,
    )

    model.total_fuel = pyo.Objective(
        expr=sum(
            model.fuel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        # Unexpected runtime errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_fuel))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}