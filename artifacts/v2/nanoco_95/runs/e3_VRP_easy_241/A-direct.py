import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    K = params["num_vehicles"]
    n = len(dist)            # 9 nodes: hub 0 + customers 1..8
    customers = list(range(1, n))
    vehicles = list(range(K))
    edges = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=list(range(n)))
    model.C = pyo.Set(initialize=customers)
    model.K = pyo.Set(initialize=vehicles)
    model.A = pyo.Set(dimen=2, initialize=edges)

    model.x = pyo.Var(model.A, model.K, domain=pyo.Binary)
    model.u = pyo.Var(model.C, model.K, domain=pyo.NonNegativeReals, bounds=(0, len(customers)))

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j, k] for (i, j) in m.A for k in m.K)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def visit_rule(m, j):
        return sum(m.x[i, j, k] for i in m.V if i != j for k in m.K) == 1
    model.visit = pyo.Constraint(model.C, rule=visit_rule)

    def flow_rule(m, j, k):
        return (sum(m.x[i, j, k] for i in m.V if i != j)
                == sum(m.x[j, i, k] for i in m.V if i != j))
    model.flow = pyo.Constraint(model.V, model.K, rule=flow_rule)

    def depot_rule(m, k):
        return sum(m.x[0, j, k] for j in m.C) <= 1
    model.depot = pyo.Constraint(model.K, rule=depot_rule)

    def mtz_rule(m, i, j, k):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[i, k] - m.u[j, k] + len(m.C) * m.x[i, j, k] <= len(m.C) - 1
    model.mtz = pyo.Constraint(model.C, model.C, model.K, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}