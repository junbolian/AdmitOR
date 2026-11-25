# IR: {"sets":{"N":"{0,...,9}","C":"N excluding depot 0","A":"{(i,j) in N x N: i != j}","P":"{(i,j) in C x C: i != j}"},"params":{"cost_matrix":"params['cost_matrix'], a 10x10 asymmetric matrix"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,9] for i in C"},"constraints":["For each i in N: sum(x[i,j] for j != i) = 1.","For each j in N: sum(x[i,j] for i != j) = 1.","For each (i,j) in P: u[i] - u[j] + 9*x[i,j] <= 8."],"objective":"Minimize sum(cost_matrix[i][j]*x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    node_count = 10
    customer_count = node_count - 1

    if len(cost_matrix) != node_count or any(
        len(row) != node_count for row in cost_matrix
    ):
        raise ValueError("cost_matrix must be a 10x10 matrix.")

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, node_count - 1)
    model.customers = pyo.RangeSet(1, customer_count)

    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(node_count)
            for j in range(node_count)
            if i != j
        ],
    )
    model.customer_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, node_count)
            for j in range(1, node_count)
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): cost_matrix[i][j]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    def outgoing_rule(block, i):
        return sum(
            block.x[i, j] for j in block.nodes if j != i
        ) == 1

    model.outgoing = pyo.Constraint(model.nodes, rule=outgoing_rule)

    def incoming_rule(block, j):
        return sum(
            block.x[i, j] for i in block.nodes if i != j
        ) == 1

    model.incoming = pyo.Constraint(model.nodes, rule=incoming_rule)

    def subtour_rule(block, i, j):
        return (
            block.u[i] - block.u[j]
            + customer_count * block.x[i, j]
            <= customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.customer_pairs,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}