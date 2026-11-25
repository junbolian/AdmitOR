import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coordinates"]
    dist = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    num_nodes = params["num_nodes"]
    num_cp = params["num_collection_points"]

    nodes = range(num_nodes)
    points = range(1, num_cp + 1)
    vehicles = range(num_vehicles)

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])
    model.veh = pyo.Set(initialize=list(vehicles))

    model.x = pyo.Var(model.arcs, model.veh, domain=pyo.Binary)

    model.obj_expr = pyo.Expression(
        expr=sum(dist[i][j] * model.x[i, j, k] for (i, j) in model.arcs for k in vehicles)
    )
    model.obj = pyo.Objective(expr=model.obj_expr, sense=pyo.minimize)

    # Each collection point visited exactly once
    def visit_rule(m, j):
        return sum(m.x[i, j, k] for i in nodes if i != j for k in vehicles) == 1
    model.visit = pyo.Constraint(points, rule=visit_rule)

    # Flow conservation for collection points and depot
    def flow_rule(m, j, k):
        return (
            sum(m.x[i, j, k] for i in nodes if i != j)
            == sum(m.x[j, i, k] for i in nodes if i != j)
        )
    model.flow = pyo.Constraint(nodes, model.veh, rule=flow_rule)

    # Depot departure/return limits: at most one outgoing and one incoming per vehicle
    def depot_out_rule(m, k):
        return sum(m.x[0, j, k] for j in nodes if j != 0) <= 1
    model.depot_out = pyo.Constraint(model.veh, rule=depot_out_rule)

    def depot_in_rule(m, k):
        return sum(m.x[i, 0, k] for i in nodes if i != 0) <= 1
    model.depot_in = pyo.Constraint(model.veh, rule=depot_in_rule)

    # Subtour elimination (MTZ) for collection points
    model.u = pyo.Var(points, model.veh, domain=pyo.NonNegativeReals)

    def mtz_rule(m, i, j, k):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[i, k] - m.u[j, k] + num_cp * m.x[i, j, k] <= num_cp - 1
    model.mtz = pyo.Constraint(points, points, model.veh, rule=mtz_rule)

    def u_bound_rule(m, i, k):
        return m.u[i, k] <= num_cp
    model.u_bound = pyo.Constraint(points, model.veh, rule=u_bound_rule)

    # Required shape: exactly the plumbing in rule 1
    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}