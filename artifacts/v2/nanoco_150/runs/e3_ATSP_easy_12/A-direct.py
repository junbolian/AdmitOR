import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    coords = params["coords"]

    num_nodes = len(cost_matrix)
    nodes = list(range(num_nodes))
    addresses = list(range(1, num_nodes))

    model = pyo.ConcreteModel()

    # Decision variables: x[i,j] = 1 if arc i->j is used
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # Disallow self-loops
    for i in nodes:
        model.x[i, i].fix(0)

    # Degree constraints (each node entered and left exactly once)
    model.in_flow = pyo.Constraint(
        nodes, rule=lambda m, j: sum(m.x[i, j] for i in nodes) == 1
    )
    model.out_flow = pyo.Constraint(
        nodes, rule=lambda m, i: sum(m.x[i, j] for j in nodes) == 1
    )

    # MTZ subtour elimination on nodes 1..n-1
    model.u = pyo.Var(addresses, bounds=(1, num_nodes - 1))
    model.mtz = pyo.Constraint(
        [(i, j) for i in addresses for j in addresses if i != j],
        rule=lambda m, i, j: m.u[i] - m.u[j] + (num_nodes - 1) * m.x[i, j]
        <= num_nodes - 2,
    )

    # Objective: minimize total travel time
    model.obj = pyo.Objective(
        expr=sum(
            cost_matrix[i][j] * model.x[i, j]
            for i in nodes
            for j in nodes
            if i != j
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}