import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    N = params["num_nodes"]
    C = params["num_customers"]
    V = params["num_vehicles"]

    customers = list(range(1, N))
    vehicles = list(range(V))
    nodes = list(range(N))

    model = pyo.ConcreteModel()

    # x[v, i, j] = 1 if vehicle v travels directly from i to j
    model.x = pyo.Var(vehicles, nodes, nodes, domain=pyo.Binary)

    # u[v, i] = position/order of customer i in vehicle v's route (MTZ)
    model.u = pyo.Var(vehicles, customers, domain=pyo.NonNegativeReals, bounds=(1, C))

    def obj_rule(m):
        return sum(
            dist[i][j] * m.x[v, i, j]
            for v in vehicles
            for i in nodes
            for j in nodes
            if i != j
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once (in-degree = 1)
    def visit_in_rule(m, j):
        return sum(m.x[v, i, j] for v in vehicles for i in nodes if i != j) == 1

    model.visit_in = pyo.Constraint(customers, rule=visit_in_rule)

    # Each customer departed exactly once (out-degree = 1)
    def visit_out_rule(m, i):
        return sum(m.x[v, i, j] for v in vehicles for j in nodes if j != i) == 1

    model.visit_out = pyo.Constraint(customers, rule=visit_out_rule)

    # Each vehicle leaves hub at most once and returns at most once
    def hub_out_rule(m, v):
        return sum(m.x[v, 0, j] for j in customers) <= 1

    model.hub_out = pyo.Constraint(vehicles, rule=hub_out_rule)

    def hub_in_rule(m, v):
        return sum(m.x[v, i, 0] for i in customers) <= 1

    model.hub_in = pyo.Constraint(vehicles, rule=hub_in_rule)

    # Flow conservation for customers per vehicle
    def flow_rule(m, v, k):
        incoming = sum(m.x[v, i, k] for i in nodes if i != k)
        outgoing = sum(m.x[v, k, j] for j in nodes if j != k)
        return incoming == outgoing

    model.flow = pyo.Constraint(vehicles, customers, rule=flow_rule)

    # MTZ subtour elimination
    def mtz_rule(m, v, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[v, i] - m.u[v, j] + C * m.x[v, i, j] <= C - 1

    model.mtz = pyo.Constraint(vehicles, customers, customers, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}