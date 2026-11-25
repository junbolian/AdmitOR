import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    K = int(params["num_vehicles"])

    # Nodes: 0 = depot, 1..8 = customers
    N = len(dist) - 1  # number of customers
    nodes = list(range(N + 1))
    customers = list(range(1, N + 1))
    vehicles = list(range(K))

    model = pyo.ConcreteModel()

    # Decision variables: x[v, i, j] = 1 if vehicle v travels arc (i, j)
    model.x = pyo.Var(vehicles, nodes, nodes, domain=pyo.Binary)
    # Ordering variable for MTZ subtour elimination: u[v, i] = position of node i in vehicle v route
    model.u = pyo.Var(vehicles, customers, domain=pyo.NonNegativeReals,
                      bounds=(1, N))

    # Objective: minimize total fleet mileage
    def obj_rule(mdl):
        return sum(dist[i][j] * mdl.x[v, i, j]
                   for v in vehicles for i in nodes for j in nodes if i != j)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once (exactly one incoming arc across fleet)
    def visit_rule(mdl, j):
        return sum(mdl.x[v, i, j]
                   for v in vehicles for i in nodes if i != j) == 1
    model.visit_con = pyo.Constraint(customers, rule=visit_rule)

    # Flow conservation at each node for each vehicle
    def flow_rule(mdl, v, h):
        return sum(mdl.x[v, i, h] for i in nodes if i != h) == \
               sum(mdl.x[v, h, j] for j in nodes if j != h)
    model.flow_con = pyo.Constraint(vehicles, nodes, rule=flow_rule)

    # Each vehicle departs depot at most once (used or not)
    def depot_out_rule(mdl, v):
        return sum(mdl.x[v, 0, j] for j in nodes if j != 0) <= 1
    model.depot_out_con = pyo.Constraint(vehicles, rule=depot_out_rule)

    # MTZ subtour elimination
    def mtz_rule(mdl, v, i, j):
        if i != j and i >= 1 and j >= 1:
            return mdl.u[v, i] - mdl.u[v, j] + N * mdl.x[v, i, j] <= N - 1
        return pyo.Constraint.Skip
    model.mtz_con = pyo.Constraint(vehicles, customers, customers, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}