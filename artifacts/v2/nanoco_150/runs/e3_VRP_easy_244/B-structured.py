# IR: {"sets":{"N":"range(num_nodes)","C":"range(1,num_customers+1)","A":"{(i,j) in N x N: i != j}","CC":"{(i,j) in C x C: i != j}"},"params":{"distance_matrix":"input arc distances","num_nodes":"input frozen node count","num_customers":"input frozen customer count","num_vehicles":"input fleet size"},"variables":{"x[i,j]":"Binary for (i,j) in A; selected directed arc","u[i]":"Real in [1,num_customers] for i in C; customer visit order"},"constraints":["sum(x[i,j] for j in N if j != i) = 1 for each i in C","sum(x[j,i] for j in N if j != i) = 1 for each i in C","sum(x[0,j] for j in C) = num_vehicles","sum(x[i,0] for i in C) = num_vehicles","u[i]-u[j]+num_customers*x[i,j] <= num_customers-1 for each (i,j) in CC"],"objective":"minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = operator.index(params["num_nodes"])
    num_customers = operator.index(params["num_customers"])
    num_vehicles = operator.index(params["num_vehicles"])

    if (num_nodes, num_customers, num_vehicles) != (9, 8, 2):
        raise ValueError("This problem requires exactly 9 nodes, 8 customers, and 2 vehicles.")
    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        raise ValueError("distance_matrix must have num_nodes rows and columns.")

    model = pyo.ConcreteModel()

    model.node_set = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.customer_set = pyo.Set(
        initialize=range(1, num_customers + 1), ordered=True
    )
    model.arc_set = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ],
    )
    model.customer_arc_set = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, num_customers + 1)
            for j in range(1, num_customers + 1)
            if i != j
        ],
    )

    model.travel_distance = pyo.Param(
        model.arc_set,
        initialize={
            (i, j): distance_matrix[i][j]
            for i, j in model.arc_set
        },
        within=pyo.NonNegativeReals,
    )
    model.customer_count = pyo.Param(initialize=num_customers)
    model.fleet_size = pyo.Param(initialize=num_vehicles)

    # Identical vehicles permit an aggregate arc formulation: the depot
    # degrees determine the number of routes, and MTZ eliminates any
    # customer-only cycles. Each resulting depot route uses one vehicle.
    model.x = pyo.Var(model.arc_set, domain=pyo.Binary)
    model.u = pyo.Var(
        model.customer_set,
        domain=pyo.Reals,
        bounds=(1, num_customers),
    )

    def customer_outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.node_set if j != i
        ) == 1

    model.customer_outgoing = pyo.Constraint(
        model.customer_set, rule=customer_outgoing_rule
    )

    def customer_incoming_rule(instance, i):
        return sum(
            instance.x[j, i] for j in instance.node_set if j != i
        ) == 1

    model.customer_incoming = pyo.Constraint(
        model.customer_set, rule=customer_incoming_rule
    )

    model.depot_departures = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.customer_set)
        == model.fleet_size
    )
    model.depot_returns = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in model.customer_set)
        == model.fleet_size
    )

    def subtour_rule(instance, i, j):
        return (
            instance.u[i]
            - instance.u[j]
            + instance.customer_count * instance.x[i, j]
            <= instance.customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.customer_arc_set, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arc_set
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when its default solution loader has no
        # feasible solution to load. Other unexpected errors propagate.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}