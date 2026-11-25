# IR: {"sets":{"N":"range(num_nodes)","B":"N excluding depot 0","A":"ordered pairs (i,j) in N x N with i != j","K":"coordinate axes {0,1}"},"params":{"num_nodes":"params['num_nodes']; frozen node count","depot_coordinates":"params['depot_coordinates']; coordinate metadata","bin_coordinates":"params['bin_coordinates']; bin coordinates in node order","distance_matrix":"params['distance_matrix']; road distances","coordinate[i,k]":"depot_coordinates[k] if i=0 else bin_coordinates[i-1][k]","distance[i,j]":"distance_matrix[i][j]"},"variables":{"x[i,j]":"Binary for (i,j) in A; selected directed arc","u[i]":"Real in [1,num_nodes-1] for i in B; visit order"},"constraints":["For each i in N: sum(x[i,j] for j in N if j!=i)=1","For each j in N: sum(x[i,j] for i in N if i!=j)=1","For each distinct i,j in B: u[i]-u[j]+(num_nodes-1)*x[i,j]<=num_nodes-2"],"objective":"Minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    depot_coordinates = params["depot_coordinates"]
    bin_coordinates = params["bin_coordinates"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.B = pyo.Set(initialize=range(1, num_nodes), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.K = pyo.Set(initialize=(0, 1), ordered=True)

    model.node_count = pyo.Param(
        initialize=num_nodes,
        within=pyo.PositiveIntegers,
        mutable=False,
    )

    def coordinate_rule(instance, i, k):
        if i == 0:
            return depot_coordinates[k]
        return bin_coordinates[i - 1][k]

    model.coordinate = pyo.Param(
        model.N,
        model.K,
        initialize=coordinate_rule,
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.A,
        initialize=lambda instance, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.B,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.N if j != i
        ) == 1

    model.departure = pyo.Constraint(model.N, rule=departure_rule)

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.N if i != j
        ) == 1

    model.arrival = pyo.Constraint(model.N, rule=arrival_rule)

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i]
            - instance.u[j]
            + (instance.node_count - 1) * instance.x[i, j]
            <= instance.node_count - 2
        )

    model.subtour = pyo.Constraint(model.B, model.B, rule=subtour_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # HiGHS raises this when it cannot load a feasible solution.
        # Other solver/runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}