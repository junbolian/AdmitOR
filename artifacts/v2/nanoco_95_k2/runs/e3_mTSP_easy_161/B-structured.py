# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"C":[1,2,3,4,5,6,7,8],"A":"{(i,j) in N x N: i != j}","B":"{(i,j) in C x C: i != j}"},"params":{"d":"params['distance_matrix']","K":"params['num_vehicles'], nonnegative integer"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous, 1 <= u[i] <= |C|, i in C"},"constraints":["sum(j in N, j != i) x[i,j] = 1 for i in C","sum(j in N, j != i) x[j,i] = 1 for i in C","sum(j in C) x[0,j] = K","sum(i in C) x[i,0] = K","u[i] - u[j] + |C|*x[i,j] <= |C|-1 for (i,j) in B"],"objective":"minimize sum((i,j) in A) d[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 8)
    model.customers = pyo.RangeSet(1, 8)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
    )
    model.customer_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.customers
            for j in model.customers
            if i != j
        ],
    )

    model.travel_distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )
    model.fleet_size = pyo.Param(
        initialize=num_vehicles,
        within=pyo.NonNegativeIntegers,
    )

    customer_count = len(model.customers)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    model.customer_departure = pyo.Constraint(
        model.customers,
        rule=lambda mdl, i: sum(
            mdl.x[i, j] for j in mdl.nodes if j != i
        ) == 1,
    )
    model.customer_arrival = pyo.Constraint(
        model.customers,
        rule=lambda mdl, i: sum(
            mdl.x[j, i] for j in mdl.nodes if j != i
        ) == 1,
    )

    # Each available vehicle operates one nonempty depot-to-depot route.
    model.depot_departure = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.customers)
        == model.fleet_size
    )
    model.depot_arrival = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in model.customers)
        == model.fleet_size
    )

    # Eliminate all cycles that do not contain the depot.
    model.subtour_elimination = pyo.Constraint(
        model.customer_arcs,
        rule=lambda mdl, i, j: (
            mdl.u[i] - mdl.u[j] + customer_count * mdl.x[i, j]
            <= customer_count - 1
        ),
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}