import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    K = int(params["num_vehicles"])

    N = len(dist)
    customers = list(range(1, N))
    nodes = list(range(N))
    vehicles = list(range(K))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, nodes, vehicles, within=pyo.Binary)

    def obj_rule(m):
        return sum(
            dist[i][j] * m.x[i, j, k]
            for i in nodes for j in nodes for k in vehicles
            if i != j
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once
    model.visit = pyo.Constraint(
        customers,
        rule=lambda m, j: sum(m.x[i, j, k] for i in nodes for k in vehicles if i != j) == 1
    )

    # Flow conservation at each customer for each vehicle
    model.flow = pyo.Constraint(
        customers, vehicles,
        rule=lambda m, j, k: sum(m.x[i, j, k] for i in nodes if i != j)
                             - sum(m.x[j, i, k] for i in nodes if i != j) == 0
    )

    # Each vehicle leaves depot at most once and returns at most once
    model.depot_out = pyo.Constraint(
        vehicles,
        rule=lambda m, k: sum(m.x[0, j, k] for j in customers) <= 1
    )
    model.depot_in = pyo.Constraint(
        vehicles,
        rule=lambda m, k: sum(m.x[i, 0, k] for i in customers) <= 1
    )

    # No self-loops
    model.noloop = pyo.Constraint(
        nodes, vehicles,
        rule=lambda m, i, k: m.x[i, i, k] == 0
    )

    # If a vehicle uses any arc, it must be balanced at depot
    model.veh_use = pyo.Constraint(
        vehicles,
        rule=lambda m, k: sum(m.x[0, j, k] for j in customers)
                          - sum(m.x[i, 0, k] for i in customers) == 0
    )

    # Lazy subtour elimination via MTZ-like ordering per vehicle
    model.u = pyo.Var(customers, vehicles, within=pyo.NonNegativeReals)

    def mtz_rule(m, i, j, k):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[i, k] - m.u[j, k] + N * m.x[i, j, k] <= N - 1

    model.mtz = pyo.Constraint(
        customers, customers, vehicles, rule=mtz_rule
    )

    model.u_lb = pyo.Constraint(
        customers, vehicles,
        rule=lambda m, i, k: m.u[i, k] >= 1
    )
    model.u_ub = pyo.Constraint(
        customers, vehicles,
        rule=lambda m, i, k: m.u[i, k] <= N
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}