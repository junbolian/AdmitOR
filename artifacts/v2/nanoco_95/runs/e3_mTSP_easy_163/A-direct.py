import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["node_coordinates"]
    dist = params["distance_matrix"]
    K = params["num_vehicles"]
    n_clinics = params["num_clinic_nodes"]

    N = len(coords)
    depots = [0]
    clinics = list(range(1, n_clinics + 1))
    nodes = list(range(N))
    vehicles = list(range(K))

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=vehicles, ordered=True)
    model.C = pyo.Set(initialize=clinics, ordered=True)
    model.N = pyo.Set(initialize=nodes, ordered=True)

    model.x = pyo.Var(model.V, model.N, model.N, domain=pyo.Binary)
    model.u = pyo.Var(model.V, model.C, domain=pyo.NonNegativeReals, bounds=(0, n_clinics))

    def obj_rule(m):
        return sum(
            dist[i][j] * m.x[k, i, j]
            for k in m.V
            for i in m.N
            for j in m.N
            if i != j
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def visit_rule(m, c):
        return sum(m.x[k, i, c] for k in m.V for i in m.N if i != c) == 1
    model.visit_once = pyo.Constraint(model.C, rule=visit_rule)

    def degree_out_rule(m, k, i):
        return sum(m.x[k, i, j] for j in m.N if j != i) == (
            1 if i == 0 else sum(m.x[k, j, i] for j in m.N if j != i)
        )
    model.degree_out = pyo.Constraint(model.V, model.N, rule=degree_out_rule)

    def in_rule(m, k, j):
        return sum(m.x[k, i, j] for i in m.N if i != j) == (
            1 if j == 0 else sum(m.x[k, j, i2] for i2 in m.N if i2 != j)
        )
    model.degree_in = pyo.Constraint(model.V, model.N, rule=in_rule)

    def depot_depart_rule(m, k):
        return sum(m.x[k, 0, j] for j in m.N if j != 0) <= 1
    model.depot_depart = pyo.Constraint(model.V, rule=depot_depart_rule)

    def depot_return_rule(m, k):
        return sum(m.x[k, i, 0] for i in m.N if i != 0) <= 1
    model.depot_return = pyo.Constraint(model.V, rule=depot_return_rule)

    def depot_out_flow_rule(m, k):
        return sum(m.x[k, 0, j] for j in m.N if j != 0) == sum(
            m.x[k, i, 0] for i in m.N if i != 0
        )
    model.depot_flow = pyo.Constraint(model.V, rule=depot_out_flow_rule)

    def mt_rule(m, k, i, j):
        if i == j or i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[k, i] - m.u[k, j] + n_clinics * m.x[k, i, j] <= n_clinics - 1
    model.mtz = pyo.Constraint(model.V, model.C, model.C, rule=mt_rule)

    def lb_rule(m, k, i):
        return m.u[k, i] >= 1
    model.u_lb = pyo.Constraint(model.V, model.C, rule=lb_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}