import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    n = len(distance)          # number of nodes including depot
    customers = list(range(1, n))
    nodes = list(range(n))
    vehicles = list(range(num_vehicles))

    # Arc set: depot->customer, customer->customer, customer->depot
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=vehicles)
    model.C = pyo.Set(initialize=customers)
    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    # x[v,i,j] = 1 if vehicle v travels arc i->j
    model.x = pyo.Var(model.V, model.A, domain=pyo.Binary)

    # u[i] = position/order of customer i on its route (MTZ subtour elimination)
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals,
                      bounds=(1, len(customers)))

    # Objective: minimize total fleet mileage
    def obj_rule(mdl):
        return sum(distance[i][j] * mdl.x[v, i, j]
                   for v in mdl.V for (i, j) in mdl.A)
    model.total_mileage = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once (in-degree = out-degree = 1)
    def visit_in_rule(mdl, j):
        return sum(mdl.x[v, i, j] for v in mdl.V for i in mdl.N if i != j) == 1
    model.visit_in = pyo.Constraint(model.C, rule=visit_in_rule)

    def visit_out_rule(mdl, i):
        return sum(mdl.x[v, i, j] for v in mdl.V for j in mdl.N if j != i) == 1
    model.visit_out = pyo.Constraint(model.C, rule=visit_out_rule)

    # Each vehicle departs depot exactly once (if used)
    def depart_rule(mdl, v):
        return sum(mdl.x[v, 0, j] for j in mdl.C) <= 1
    model.depart = pyo.Constraint(model.V, rule=depart_rule)

    # Each vehicle returns to depot exactly once
    def return_rule(mdl, v):
        return sum(mdl.x[v, i, 0] for i in mdl.C) <= 1
    model.ret = pyo.Constraint(model.V, rule=return_rule)

    # Flow conservation at customers per vehicle
    def flow_rule(mdl, v, k):
        inflow = sum(mdl.x[v, i, k] for i in mdl.N if i != k)
        outflow = sum(mdl.x[v, k, j] for j in mdl.N if j != k)
        return inflow == outflow
    model.flow = pyo.Constraint(model.V, model.C, rule=flow_rule)

    # Subtour elimination (MTZ) using u variables
    M = len(customers)
    big = len(customers) + 1

    def mtz_rule(mdl, v, i, j):
        if i != j:
            return mdl.u[i] - mdl.u[j] + big * mdl.x[v, i, j] <= M
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(model.V,
                               pyo.Set(initialize=customers, dimen=1) * pyo.Set(initialize=customers, dimen=1),
                               rule=mtz_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_mileage))
    return {"objective": obj_val, "status": "optimal"}