import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    K = params["fleet_size"]

    N = len(dist)
    customers = list(range(1, N))  # nodes 1..8
    nodes = list(range(N))

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes)
    model.C = pyo.Set(initialize=customers)
    model.K = pyo.Set(initialize=list(range(K)))

    model.x = pyo.Var(model.V, model.V, model.K, domain=pyo.Binary)
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            dist[i][j] * m.x[i, j, k]
            for i in m.V for j in m.V for k in m.K
            if i != j
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once
    def visit_once_rule(m, j):
        return sum(m.x[i, j, k] for i in m.V if i != j for k in m.K) == 1
    model.visit_once = pyo.Constraint(model.C, rule=visit_once_rule)

    # Flow conservation per vehicle
    def flow_rule(m, c, k):
        out_ = sum(m.x[c, j, k] for j in m.V if j != c)
        in_ = sum(m.x[i, c, k] for i in m.V if i != c)
        return out_ == in_
    model.flow = pyo.Constraint(model.C, model.K, rule=flow_rule)

    # Each vehicle leaves depot at most once
    def depot_out_rule(m, k):
        return sum(m.x[0, j, k] for j in m.V if j != 0) <= 1
    model.depot_out = pyo.Constraint(model.K, rule=depot_out_rule)

    # Depot flow balance
    def depot_bal_rule(m, k):
        out_ = sum(m.x[0, j, k] for j in m.V if j != 0)
        in_ = sum(m.x[i, 0, k] for i in m.V if i != 0)
        return out_ == in_
    model.depot_bal = pyo.Constraint(model.K, rule=depot_bal_rule)

    # MTZ subtour elimination
    def mtz_rule(m, i, j, k):
        if i == j or i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (N - 1) * m.x[i, j, k] <= (N - 2)
    model.mtz = pyo.Constraint(model.C, model.C, model.K, rule=mtz_rule)

    def u_lb_rule(m, i):
        return m.u[i] >= 1
    model.u_lb = pyo.Constraint(model.C, rule=u_lb_rule)

    def u_ub_rule(m, i):
        return m.u[i] <= N - 1
    model.u_ub = pyo.Constraint(model.C, rule=u_ub_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}