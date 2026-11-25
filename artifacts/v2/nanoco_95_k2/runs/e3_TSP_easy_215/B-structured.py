# IR: {"sets":{"N":"{0,...,8}","C":"N \\ {0}","A":"{(i,j) in N x N: i != j}","K":"{0,1}"},"params":{"distance_matrix":"distance_matrix[i][j] from params; nonnegative arc costs","node_coordinates":"node_coordinates[i][k] from params; informational Cartesian coordinates"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,|C|] for i in C"},"constraints":["For each i in N: sum(x[i,j] for j in N if j != i) = 1.","For each j in N: sum(x[i,j] for i in N if i != j) = 1.","For distinct i,j in C: u[i] - u[j] + |C|*x[i,j] <= |C|-1."],"objective":"Minimize sum(distance_matrix[i,j]*x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    model = pyo.ConcreteModel()

    model.N = pyo.RangeSet(0, 8)
    model.C = pyo.RangeSet(1, 8)
    model.K = pyo.RangeSet(0, 1)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.N
            for j in model.N
            if i != j
        ],
    )

    model.distance_matrix = pyo.Param(
        model.A,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )
    model.node_coordinates = pyo.Param(
        model.N,
        model.K,
        initialize=lambda mdl, i, k: node_coordinates[i][k],
        within=pyo.Reals,
    )

    customer_count = len(model.C)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    def departure_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.N if j != i) == 1

    model.departure_constraints = pyo.Constraint(
        model.N, rule=departure_rule
    )

    def arrival_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.N if i != j) == 1

    model.arrival_constraints = pyo.Constraint(
        model.N, rule=arrival_rule
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i] - mdl.u[j] + customer_count * mdl.x[i, j]
            <= customer_count - 1
        )

    model.subtour_constraints = pyo.Constraint(
        model.C, model.C, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance_matrix[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}