import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    required = [tuple(e) for e in params["required_edge_set"]]

    n = len(dist)
    nodes = list(range(n))
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, domain=pyo.NonNegativeReals)

    # Degree balance at every node
    model.balance = pyo.ConstraintList()
    for k in nodes:
        model.balance.add(
            sum(model.x[i, j] for (i, j) in edges if i == k)
            == sum(model.x[i, j] for (i, j) in edges if j == k)
        )

    # Each required edge (in its given orientation) served at least once
    model.service = pyo.ConstraintList()
    for (u, v) in required:
        model.service.add(model.x[u, v] >= 1)

    # Depot / connectivity: at least one departure from depot
    model.depot = pyo.Constraint(expr=sum(model.x[0, j] for j in nodes if j != 0) >= 1)

    # Connectivity / subtour elimination via single-commodity flow
    # One unit of commodity originates at the depot for each required edge unit
    total_service = len(required)
    model.y = pyo.Var(edges, domain=pyo.NonNegativeReals)

    model.flow = pyo.ConstraintList()
    for k in nodes:
        inflow = sum(model.y[i, j] for (i, j) in edges if j == k)
        outflow = sum(model.y[i, j] for (i, j) in edges if i == k)
        if k == 0:
            model.flow.add(outflow - inflow == total_service)
        else:
            demand = sum(1 for (u, v) in required if v == k)
            model.flow.add(outflow - inflow == -demand)

    # Link flow to traversal (capacity)
    model.link = pyo.ConstraintList()
    for (i, j) in edges:
        model.link.add(model.y[i, j] <= total_service * model.x[i, j])

    model.obj = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in edges),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}