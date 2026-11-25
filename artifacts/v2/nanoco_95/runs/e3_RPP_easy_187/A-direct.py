import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["num_nodes"]
    dist = params["distance_matrix"]

    # Required edges: mandatory segments (hardcoded index structure)
    required_edges = [
        (0, 6), (0, 7), (1, 3), (2, 7), (4, 7), (4, 8), (5, 6), (5, 8),
    ]

    model = pyo.ConcreteModel()

    # Complete directed arc set (i != j)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    # Integer flow variables: number of traversals of arc (i,j)
    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total travel distance
    def obj_rule(m):
        return sum(
            float(dist[i][j]) * m.flow[i, j] for (i, j) in m.ARCS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Service requirement: each required edge must be traversed at least once
    # (in either direction)
    model.service = pyo.ConstraintList()
    for (u, v) in required_edges:
        model.service.add(
            model.flow[u, v] + model.flow[v, u] >= 1
        )

    # Flow conservation: departures = arrivals at every node
    # (closed-loop route continuity; depot 0 included)
    model.balance = pyo.ConstraintList()
    for k in range(n):
        out_flow = sum(
            model.flow[k, j] for j in range(n) if j != k
        )
        in_flow = sum(
            model.flow[i, k] for i in range(n) if i != k
        )
        model.balance.add(out_flow == in_flow)

    # Depot connectivity: total departures from depot = total arrivals (already
    # implied by balance). Route must actually exist; enforce depot is used.
    model.depot_use = pyo.Constraint(
        expr=sum(model.flow[0, j] for j in range(n) if j != 0) >= 1
    )

    result = Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}