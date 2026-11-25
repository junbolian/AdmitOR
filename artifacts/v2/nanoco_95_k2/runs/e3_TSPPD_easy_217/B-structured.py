# IR: {"sets":{"V":"range(num_nodes)","C":"V excluding 0","A":"{(i,j) in V x V: i != j}","K":"range(num_pairs)","pairs":[[4,5],[6,1],[2,3]]},"params":{"distance_matrix":"params['distance_matrix']","num_nodes":"params['num_nodes']","num_pairs":"params['num_pairs']"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,num_nodes-1] for i in C"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1","For each j in V: sum(x[i,j] for i != j) = 1","For distinct i,j in C: u[i]-u[j]+num_nodes*x[i,j] <= num_nodes-1","For each k in K with (pickup,delivery)=pairs[k]: u[pickup]+1 <= u[delivery]"],"objective":"minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]

    pickup_delivery_pairs = ((4, 5), (6, 1), (2, 3))

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(num_nodes), ordered=True)
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

    model.fuel_cost = pyo.Param(
        model.A,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.V if j != i) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.V if i != j) == 1

    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i] - mdl.u[j] + num_nodes * mdl.x[i, j]
            <= num_nodes - 1
        )

    model.subtour = pyo.Constraint(model.C, model.C, rule=subtour_rule)

    def precedence_rule(mdl, k):
        pickup, delivery = pickup_delivery_pairs[k]
        return mdl.u[pickup] + 1 <= mdl.u[delivery]

    model.precedence = pyo.Constraint(model.K, rule=precedence_rule)

    model.total_fuel_cost = pyo.Objective(
        expr=sum(
            model.fuel_cost[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi raises RuntimeError when no feasible solution can be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_fuel_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}