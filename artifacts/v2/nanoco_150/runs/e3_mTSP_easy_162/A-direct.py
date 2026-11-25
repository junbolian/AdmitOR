import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_vehicles = int(params["num_vehicles"])
    num_customers = int(params["num_customers"])
    depot_x = params["depot_x"]
    depot_y = params["depot_y"]
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]
    distance_matrix = params["distance_matrix"]

    nodes = list(range(num_customers + 1))
    customers = list(range(1, num_customers + 1))
    vehicles = list(range(num_vehicles))

    # Build a distance dict from the provided matrix (keeps params-driven data).
    dist = {}
    for i in nodes:
        for j in nodes:
            dist[(i, j)] = distance_matrix[i][j]

    depot = 0

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.CUST = pyo.Set(initialize=customers)
    model.VEH = pyo.Set(initialize=vehicles)
    model.ARCS = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])

    # x[v, i, j] = 1 if vehicle v traverses arc (i, j)
    model.x = pyo.Var(model.VEH, model.ARCS, domain=pyo.Binary)

    # Objective: total distance travelled by all vehicles.
    def obj_rule(m):
        return sum(
            dist[(i, j)] * m.x[v, i, j]
            for v in m.VEH
            for (i, j) in m.ARCS
        )

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once (entered exactly once).
    def visit_in_rule(m, c):
        return sum(m.x[v, i, c] for v in m.VEH for i in m.NODES if i != c) == 1

    model.visit_in = pyo.Constraint(model.CUST, rule=visit_in_rule)

    # Flow conservation for every vehicle at every node.
    def flow_rule(m, v, k):
        return (
            sum(m.x[v, i, k] for i in m.NODES if i != k)
            - sum(m.x[v, k, j] for j in m.NODES if j != k)
            == 0
        )

    model.flow = pyo.Constraint(model.VEH, model.NODES, rule=flow_rule)

    # Each vehicle leaves the depot at most once.
    def depot_out_rule(m, v):
        return sum(m.x[v, depot, j] for j in m.NODES if j != depot) <= 1

    model.depot_out = pyo.Constraint(model.VEH, rule=depot_out_rule)

    # Each vehicle returns to the depot at most once.
    def depot_in_rule(m, v):
        return sum(m.x[v, i, depot] for i in m.NODES if i != depot) <= 1

    model.depot_in = pyo.Constraint(model.VEH, rule=depot_in_rule)

    # Subtour elimination (single-commodity flow).
    # u[v, c] = load/order variable for customer c on vehicle v.
    model.u = pyo.Var(model.VEH, model.CUST, bounds=(1, num_customers))

    def subtour_rule(m, v, i, j):
        if j == depot:
            return pyo.Constraint.Skip
        return m.u[v, j] >= m.u[v, i] + 1 - num_customers * (1 - m.x[v, i, j])

    model.subtour = pyo.Constraint(
        model.VEH,
        [(i, j) for (i, j) in model.ARCS if i in customers],
        rule=subtour_rule,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}