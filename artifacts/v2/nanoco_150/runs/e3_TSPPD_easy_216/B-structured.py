# IR: {"sets":{"N":[0,1,2,3,4,5,6],"C":[1,2,3,4,5,6],"A":"{(i,j) in N x N: i != j}","P":[[6,2],[5,4],[1,3]]},"params":{"distance[i,j]":"params['dist_min(i,j)_max(i,j)'] for every (i,j) in A; symmetric"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [1,6] for i in C"},"constraints":["For each i in N: sum(x[i,j] for j in N if j != i) = 1","For each j in N: sum(x[i,j] for i in N if i != j) = 1","For distinct i,j in C: u[i] - u[j] + 6*x[i,j] <= 5","For each (pickup,delivery) in P: u[pickup] + 1 <= u[delivery]"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = tuple(range(7))
    customers = tuple(range(1, 7))
    arcs = tuple((i, j) for i in nodes for j in nodes if i != j)
    pairs = ((6, 2), (5, 4), (1, 3))
    customer_count = len(customers)

    undirected_distances = {
        (0, 1): params["dist_0_1"],
        (0, 2): params["dist_0_2"],
        (0, 3): params["dist_0_3"],
        (0, 4): params["dist_0_4"],
        (0, 5): params["dist_0_5"],
        (0, 6): params["dist_0_6"],
        (1, 2): params["dist_1_2"],
        (1, 3): params["dist_1_3"],
        (1, 4): params["dist_1_4"],
        (1, 5): params["dist_1_5"],
        (1, 6): params["dist_1_6"],
        (2, 3): params["dist_2_3"],
        (2, 4): params["dist_2_4"],
        (2, 5): params["dist_2_5"],
        (2, 6): params["dist_2_6"],
        (3, 4): params["dist_3_4"],
        (3, 5): params["dist_3_5"],
        (3, 6): params["dist_3_6"],
        (4, 5): params["dist_4_5"],
        (4, 6): params["dist_4_6"],
        (5, 6): params["dist_5_6"],
    }

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.P = pyo.Set(dimen=2, initialize=pairs, ordered=True)
    model.customer_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j) for i in customers for j in customers if i != j
        ],
    )

    model.distance = pyo.Param(
        model.A,
        initialize={
            (i, j): undirected_distances[(min(i, j), max(i, j))]
            for i, j in arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Integers,
        bounds=(1, customer_count),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.N if j != i
        ) == 1

    model.outgoing = pyo.Constraint(model.N, rule=outgoing_rule)

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.N if i != j
        ) == 1

    model.incoming = pyo.Constraint(model.N, rule=incoming_rule)

    def subtour_rule(instance, i, j):
        return (
            instance.u[i]
            - instance.u[j]
            + customer_count * instance.x[i, j]
            <= customer_count - 1
        )

    model.subtour = pyo.Constraint(
        model.customer_arcs,
        rule=subtour_rule,
    )

    def precedence_rule(instance, pickup, delivery):
        return instance.u[pickup] + 1 <= instance.u[delivery]

    model.precedence = pyo.Constraint(model.P, rule=precedence_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}