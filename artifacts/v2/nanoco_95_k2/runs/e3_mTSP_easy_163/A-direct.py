import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Nodes: 0 = depot, 1..8 = clinics
    clinics = list(range(1, 9))
    nodes = [0] + clinics
    K = range(params["num_vehicles"])
    V = [ (i, j) for i in nodes for j in nodes if i != j ]

    # Build distance dictionary from params
    dist = {}
    for i, j in V:
        a, b = (i, j) if i < j else (j, i)
        dist[(i, j)] = params["dist_%d_%d" % (a, b)]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.CLINICS = pyo.Set(initialize=clinics)
    model.VEH = pyo.Set(initialize=list(K))
    model.ARCS = pyo.Set(initialize=V, dimen=2)

    model.x = pyo.Var(model.VEH, model.ARCS, domain=pyo.Binary)
    model.u = pyo.Var(model.VEH, model.CLINICS, domain=pyo.NonNegativeReals, bounds=(1, 8))

    # Objective: minimize total distance
    def obj_rule(m):
        return sum(dist[(i, j)] * m.x[k, i, j] for k in m.VEH for (i, j) in m.ARCS)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each clinic visited exactly once
    def visit_rule(m, j):
        return sum(m.x[k, i, j] for k in m.VEH for i in m.NODES if i != j) == 1
    model.visit = pyo.Constraint(model.CLINICS, rule=visit_rule)

    # Flow conservation at each node for each vehicle
    def flow_rule(m, k, j):
        return (sum(m.x[k, i, j] for i in m.NODES if i != j)
                == sum(m.x[k, j, l] for l in m.NODES if l != j))
    model.flow = pyo.Constraint(model.VEH, model.NODES, rule=flow_rule)

    # Depot: each vehicle leaves at most once
    def depot_out_rule(m, k):
        return sum(m.x[k, 0, j] for j in m.CLINICS) <= 1
    model.depot_out = pyo.Constraint(model.VEH, rule=depot_out_rule)

    # MTZ subtour elimination
    def mtz_rule(m, k, i, j):
        if i == j:
            return pyo.Constraint.Skip
        if i in clinics and j in clinics:
            return m.u[k, i] - m.u[k, j] + 8 * m.x[k, i, j] <= 7
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(model.VEH, model.ARCS, rule=mtz_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}