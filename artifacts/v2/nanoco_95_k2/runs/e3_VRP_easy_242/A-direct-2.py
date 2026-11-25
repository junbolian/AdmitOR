import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_clinics = 8
    nodes = list(range(n_clinics + 1))  # 0 = depot, 1..8 = clinics
    clinics = list(range(1, n_clinics + 1))
    num_vehicles = 2

    # Build symmetric distance dict from params
    dist = {}
    dist[0, 0] = 0.0
    for j in clinics:
        dist[0, j] = params["dist_0_%d" % j]
        dist[j, 0] = params["dist_0_%d" % j]
    for i in clinics:
        dist[i, i] = 0.0
        for j in clinics:
            if j > i:
                dist[i, j] = params["dist_%d_%d" % (i, j)]
                dist[j, i] = params["dist_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    # Arc set
    arc_list = [(i, j) for i in nodes for j in nodes if i != j]
    model.ARC = pyo.Set(initialize=arc_list, dimen=2)
    model.CUST = pyo.Set(initialize=clinics)

    model.x = pyo.Var(model.ARC, domain=pyo.Binary)
    model.u = pyo.Var(model.CUST, domain=pyo.NonNegativeReals, bounds=(1, n_clinics))

    def obj_rule(m):
        return sum(dist[i, j] * m.x[i, j] for (i, j) in m.ARC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each clinic has exactly one incoming and one outgoing arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1

    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1

    model.in_con = pyo.Constraint(model.CUST, rule=in_rule)
    model.out_con = pyo.Constraint(model.CUST, rule=out_rule)

    # Depot: exactly num_vehicles depart and return
    def depot_out_rule(m):
        return sum(m.x[0, j] for j in m.CUST) == num_vehicles

    def depot_in_rule(m):
        return sum(m.x[i, 0] for i in m.CUST) == num_vehicles

    model.depot_out_con = pyo.Constraint(rule=depot_out_rule)
    model.depot_in_con = pyo.Constraint(rule=depot_in_rule)

    # Subtour elimination (MTZ)
    def mtz_rule(m, i, j):
        if i != j and i in clinics and j in clinics:
            return m.u[i] - m.u[j] + n_clinics * m.x[i, j] <= n_clinics - 1
        return pyo.Constraint.Skip

    model.mtz_con = pyo.Constraint(model.ARC, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}