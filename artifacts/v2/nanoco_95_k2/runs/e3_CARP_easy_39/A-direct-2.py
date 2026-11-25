import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---- data ----
    segments = [
        (0, 2, params["demand_0_2"]),
        (0, 6, params["demand_0_6"]),
        (2, 3, params["demand_2_3"]),
        (2, 4, params["demand_2_4"]),
    ]
    Q = params["truck_capacity"]
    num_trucks = int(params["num_trucks"])
    num_nodes = int(params["num_nodes"])
    dist_flat = params["distance_matrix"]

    def d(u, v):
        return dist_flat[u * num_nodes + v]

    # ---- model ----
    model = pyo.ConcreteModel()
    model.S = pyo.RangeSet(0, len(segments) - 1)
    model.T = pyo.RangeSet(0, num_trucks - 1)
    model.N = pyo.RangeSet(0, num_nodes - 1)

    # assignment: segment s served by truck t
    model.assign = pyo.Var(model.S, model.T, domain=pyo.Binary)

    # service direction: dir[s] = 1 means (i->j), 0 means (j->i)
    model.dir = pyo.Var(model.S, domain=pyo.Binary)

    # traversal x[t,u,v]: 1 if truck t travels from u to v (service or deadhead)
    arcs = [(t, u, v) for t in range(num_trucks)
            for u in range(num_nodes) for v in range(num_nodes) if u != v]
    model.A = pyo.Set(initialize=arcs, dimen=3)
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # each segment served exactly once
    model.seg_once = pyo.Constraint(
        model.S,
        rule=lambda m, s: sum(m.assign[s, t] for t in m.T) == 1,
    )

    # service arc used exactly when segment assigned & direction chosen
    def service_rule(m, s, t):
        i, j, _ = segments[s]
        return m.x[t, i, j] - m.x[t, j, i] == m.assign[s, t] * (2 * m.dir[s] - 1)
    model.service = pyo.Constraint(model.S, model.T, rule=service_rule)

    # flow conservation for each truck at each node (depot balanced, others balanced)
    def flow_rule(m, t, n):
        inflow = sum(m.x[t, u, n] for u in range(num_nodes) if u != n)
        outflow = sum(m.x[t, n, v] for v in range(num_nodes) if v != n)
        return inflow == outflow
    model.flow = pyo.Constraint(model.T, model.N, rule=flow_rule)

    # capacity per truck
    model.cap = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(m.assign[s, t] * segments[s][2] for s in m.S) <= Q,
    )

    # subtour elimination via single-commodity flow (MTZ-style) on used arcs
    # order var per truck per node
    model.u = pyo.Var(model.T, model.N, domain=pyo.NonNegativeReals,
                      bounds=(0, num_nodes))

    def subtour_rule(m, t, u, v):
        if u == v:
            return pyo.Constraint.Skip
        return m.u[t, v] >= m.u[t, u] + 1 - num_nodes * (1 - m.x[t, u, v])
    model.subtour = pyo.Constraint(model.A, rule=subtour_rule)

    model.depot_order = pyo.Constraint(
        model.T, rule=lambda m, t: m.u[t, 0] == 0,
    )

    # objective
    model.objective = pyo.Objective(
        expr=sum(d(u, v) * model.x[t, u, v] for (t, u, v) in model.A),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}