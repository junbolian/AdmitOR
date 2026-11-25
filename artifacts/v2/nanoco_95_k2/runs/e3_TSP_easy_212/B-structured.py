# IR: {"sets":{"N":"0,...,num_nodes-1","B":"N excluding depot 0","A":"(i,j) in N x N with i != j","D":[0,1]},"params":{"num_nodes":"params['num_nodes']","depot_coordinates":"params['depot_coordinates']; coordinate metadata","bin_coordinates":"params['bin_coordinates']; coordinates for nodes 1,...,num_nodes-1","distance_matrix":"params['distance_matrix']; authoritative arc costs"},"variables":{"x[i,j]":"binary for (i,j) in A; arc selected","u[i]":"continuous in [1,num_nodes-1] for i in B; visit order"},"constraints":["For each i in N: sum(x[i,j] for j in N if j != i) = 1.","For each j in N: sum(x[i,j] for i in N if i != j) = 1.","For distinct i,j in B: u[i] - u[j] + (num_nodes-1)*x[i,j] <= num_nodes-2."],"objective":"Minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    depot_coordinates = params["depot_coordinates"]
    bin_coordinates = params["bin_coordinates"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.bins = pyo.RangeSet(1, num_nodes - 1)
    model.coordinate_axes = pyo.Set(initialize=[0, 1], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ],
    )

    # Coordinates are metadata; road distances determine the objective.
    def coordinate_rule(instance, i, axis):
        if i == 0:
            return depot_coordinates[axis]
        return bin_coordinates[i - 1][axis]

    model.node_coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize=coordinate_rule,
        within=pyo.Reals,
    )
    model.road_distance = pyo.Param(
        model.arcs,
        initialize=lambda instance, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.bins,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.nodes if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.nodes, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.nodes if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.nodes, rule=arrival_rule
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
        model.bins, model.bins, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.road_distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Selected arcs encode the complete sequence starting and ending at 0.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}