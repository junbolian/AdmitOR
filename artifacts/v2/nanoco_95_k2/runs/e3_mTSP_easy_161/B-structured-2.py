# IR: {"sets":{"N":"{0,...,8}","C":"{1,...,8}","A":"{(i,j) in N x N: i != j}","B":"{(i,j) in C x C: i != j}"},"params":{"distance_matrix":"params['distance_matrix'], indexed by N x N","num_vehicles":"params['num_vehicles'], nonnegative integer"},"variables":{"x[i,j]":"binary for (i,j) in A; selected directed route arc","u[i]":"continuous in [1,8] for i in C; customer visit order"},"constraints":["For each i in C: sum(x[i,j] for j in N if j != i) = 1","For each j in C: sum(x[i,j] for i in N if i != j) = 1","sum(x[0,j] for j in C) = num_vehicles","sum(x[i,0] for i in C) = num_vehicles","For each (i,j) in B: u[i] - u[j] + 8*x[i,j] <= 7"],"objective":"Minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

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
            for i in range(9)
            for j in range(9)
            if i != j
        ],
    )
    model.customer_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 9)
            for j in range(1, 9)
            if i != j
        ],
    )

    model.travel_distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in range(9)
            for j in range(9)
        },
        within=pyo.Reals,
    )
    model.fleet_size = pyo.Param(
        initialize=num_vehicles,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, 8),
    )

    def customer_departure_rule(instance, i):
        return sum(
            instance.x[i, j]
            for j in instance.nodes
            if j != i
        ) == 1

    model.customer_departure = pyo.Constraint(
        model.customers,
        rule=customer_departure_rule,
    )

    def customer_arrival_rule(instance, j):
        return sum(
            instance.x[i, j]
            for i in instance.nodes
            if i != j
        ) == 1

    model.customer_arrival = pyo.Constraint(
        model.customers,
        rule=customer_arrival_rule,
    )

    model.depot_departure = pyo.Constraint(
        expr=sum(
            model.x[0, j] for j in model.customers
        ) == model.fleet_size
    )
    model.depot_arrival = pyo.Constraint(
        expr=sum(
            model.x[i, 0] for i in model.customers
        ) == model.fleet_size
    )

    def subtour_elimination_rule(instance, i, j):
        return (
            instance.u[i] - instance.u[j] + 8 * instance.x[i, j]
            <= 7
        )

    model.subtour_elimination = pyo.Constraint(
        model.customer_arcs,
        rule=subtour_elimination_rule,
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}