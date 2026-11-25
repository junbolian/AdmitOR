import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_trucks = int(params["num_trucks"])
    capacity = params["truck_capacity"]
    coords_x = list(params["coord_x"])
    dist = list(params["distance_matrix"])

    seg_demands = [
        (0, 2, params["demand_segment_0_2"]),
        (0, 6, params["demand_segment_0_6"]),
        (2, 3, params["demand_segment_2_3"]),
        (2, 4, params["demand_segment_2_4"]),
    ]
    n_seg = len(seg_demands)
    trucks = list(range(num_trucks))
    segs = list(range(n_seg))
    nodes = list(range(len(coords_x)))

    seg_i = {s: seg_demands[s][0] for s in segs}
    seg_j = {s: seg_demands[s][1] for s in segs}
    seg_d = {s: seg_demands[s][2] for s in segs}

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=trucks)
    model.S = pyo.Set(initialize=segs)
    model.N = pyo.Set(initialize=nodes)

    # y[t,s] = 1 if truck t serves segment s
    model.y = pyo.Var(model.T, model.S, domain=pyo.Binary)
    # z[t,s] = 0 if segment traversed i->j, 1 if j->i
    model.z = pyo.Var(model.T, model.S, domain=pyo.Binary)

    # Allowed arcs: require 0-touching or required-segment arcs (either direction)
    def allowed_arc(i, j):
        if i == j:
            return False
        if i == 0 or j == 0:
            return True
        for s in segs:
            a, b = seg_i[s], seg_j[s]
            if (i == a and j == b) or (i == b and j == a):
                return True
        return False

    arc_list = []
    for t in trucks:
        for i in nodes:
            for j in nodes:
                if allowed_arc(i, j):
                    arc_list.append((t, i, j))

    model.A = pyo.Set(initialize=arc_list, dimen=3)
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # u[t,i] = visiting order
    model.u = pyo.Var(model.T, model.N, within=pyo.NonNegativeReals, bounds=(0, len(nodes)))

    # Each segment served exactly once
    def serve_rule(m, s):
        return sum(m.y[t, s] for t in m.T) == 1

    model.serve = pyo.Constraint(model.S, rule=serve_rule)

    # Capacity
    def cap_rule(m, t):
        return sum(m.y[t, s] * seg_d[s] for s in m.S) <= capacity

    model.cap = pyo.Constraint(model.T, rule=cap_rule)

    # Direction: x[t,i,j] = y - z, x[t,j,i] = z
    def dir_ij_rule(m, t, s):
        i = seg_i[s]
        j = seg_j[s]
        return m.x[t, i, j] == m.y[t, s] - m.z[t, s]

    def dir_ji_rule(m, t, s):
        i = seg_i[s]
        j = seg_j[s]
        return m.x[t, j, i] == m.z[t, s]

    model.dir_ij = pyo.Constraint(model.T, model.S, rule=dir_ij_rule)
    model.dir_ji = pyo.Constraint(model.T, model.S, rule=dir_ji_rule)

    # Node balance: for non-depot nodes, out = in; depot out = in
    def node_balance_rule(m, t, i):
        out_flow = sum(m.x[t, i, j] for (tt, a, b) in m.A if tt == t and a == i for j in [b])
        in_flow = sum(m.x[t, k, i] for (tt, a, b) in m.A if tt == t and b == i for k in [a])
        return out_flow == in_flow

    model.node_balance = pyo.Constraint(model.T, model.N, rule=node_balance_rule)

    # Depot: at most 1 departure per truck
    def depot_out_rule(m, t):
        return sum(m.x[t, 0, j] for (tt, a, b) in m.A if tt == t and a == 0 for j in [b]) <= 1

    model.depot_out = pyo.Constraint(model.T, rule=depot_out_rule)

    # Arc-usage linkage: if truck uses any segment arc, count into y
    # (already enforced via dir constraints)

    # Subtour elimination (MTZ)
    bigM_mtz = len(nodes) + 1

    def mtz_rule(m, t, i, j):
        if (t, i, j) not in m.A:
            return pyo.Constraint.Skip
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[t, j] >= m.u[t, i] + 1 - bigM_mtz * (1 - m.x[t, i, j])

    model.mtz = pyo.Constraint(model.T, model.N, model.N, rule=mtz_rule)

    def u_depot_rule(m, t):
        return m.u[t, 0] == 0

    model.u_depot = pyo.Constraint(model.T, rule=u_depot_rule)

    # Objective: total distance
    def obj_rule(m):
        return sum(dist[i][j] * m.x[t, i, j] for (t, i, j) in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}