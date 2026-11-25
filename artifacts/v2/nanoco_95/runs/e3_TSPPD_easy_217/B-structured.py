# IR: {"sets":{"N":"range(num_nodes)","C":"N excluding 0","A":"{(i,j) in N x N: i != j}","K":"range(num_pairs)"},"params":{"num_nodes":"params['num_nodes']","num_pairs":"params['num_pairs']","distance_matrix":"params['distance_matrix']","pickup_delivery_pairs":"params['pickup_delivery_pairs']"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,num_nodes-1] for i in C"},"constraints":["For each i in N: sum(x[i,j] for j != i) = 1.","For each j in N: sum(x[i,j] for i != j) = 1.","For distinct i,j in C: u[i]-u[j]+(num_nodes-1)*x[i,j] <= num_nodes-2.","For each k in K with pair (p,d): u[p]+1 <= u[d]."],"objective":"Minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]
    distance_matrix = params["distance_matrix"]
    pickup_delivery_pairs = params["pickup_delivery_pairs"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.C = pyo.Set(initialize=range(1, num_nodes), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.K = pyo.Set(initialize=range(num_pairs), ordered=True)

    model.travel_cost = pyo.Param(
        model.A,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.N if j != i
        ) == 1

    model.outgoing_arc = pyo.Constraint(model.N, rule=outgoing_rule)

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.N if i != j
        ) == 1

    model.incoming_arc = pyo.Constraint(model.N, rule=incoming_rule)

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i]
            - instance.u[j]
            + (num_nodes - 1) * instance.x[i, j]
            <= num_nodes - 2
        )

    model.subtour_elimination = pyo.Constraint(
        model.C, model.C, rule=subtour_rule
    )

    def precedence_rule(instance, k):
        pickup, delivery = pickup_delivery_pairs[k]
        return instance.u[pickup] + 1 <= instance.u[delivery]

    model.pickup_precedence = pyo.Constraint(
        model.K, rule=precedence_rule
    )

    model.total_fuel_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_fuel_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}