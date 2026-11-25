import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    D = params["distance_matrix"]
    segs = params["segment_demands"]
    cap = params["vehicle_capacity"]
    n = len(D)
    K = 2
    depot = 0
    S = list(range(len(segs)))

    # segs entries may be ((i,j), demand) or (i, j, demand); normalize.
    seg_ends = []
    seg_dem = []
    for s in segs:
        if len(s) == 2:
            pair, dem = s
            seg_ends.append((int(pair[0]), int(pair[1])))
            seg_dem.append(float(dem))
        else:
            seg_ends.append((int(s[0]), int(s[1])))
            seg_dem.append(float(s[2]))

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    model.K = pyo.RangeSet(0, K - 1)
    model.S = pyo.RangeSet(0, len(S) - 1)
    model.N = pyo.RangeSet(0, n - 1)
    model.A = pyo.Set(initialize=arcs, dimen=2)
    model.DIR = pyo.Set(initialize=[0, 1])

    model.x = pyo.Var(model.K, model.A, domain=pyo.Binary)
    model.z = pyo.Var(model.K, model.S, model.DIR, domain=pyo.Binary)
    model.f = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.K, model.N, domain=pyo.Binary)

    def obj_rule(m):
        return sum(D[i][j] * m.x[k, i, j] for k in m.K for (i, j) in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def seg_once_rule(m, s):
        return sum(m.z[k, s, d] for k in m.K for d in m.DIR) == 1
    model.seg_once = pyo.Constraint(model.S, rule=seg_once_rule)

    def cap_rule(m, k):
        return sum(seg_dem[s] * m.z[k, s, d] for s in m.S for d in m.DIR) <= cap
    model.cap_con = pyo.Constraint(model.K, rule=cap_rule)

    def link_rule(m, k, s, d):
        a, b = seg_ends[s]
        if d == 1:
            a, b = b, a
        return m.x[k, a, b] >= m.z[k, s, d]
    model.link = pyo.Constraint(model.K, model.S, model.DIR, rule=link_rule)

    def balance_rule(m, k, v):
        return (sum(m.x[k, i, v] for i in range(n) if i != v)
                == sum(m.x[k, v, j] for j in range(n) if j != v))
    model.balance = pyo.Constraint(model.K, model.N, rule=balance_rule)

    def y_link_in(m, k, v):
        return sum(m.x[k, i, v] for i in range(n) if i != v) <= n * m.y[k, v]
    def y_link_out(m, k, v):
        return sum(m.x[k, v, j] for j in range(n) if j != v) <= n * m.y[k, v]
    model.y_in = pyo.Constraint(model.K, model.N, rule=y_link_in)
    model.y_out = pyo.Constraint(model.K, model.N, rule=y_link_out)

    def flow_con(m, k, v):
        if v == depot:
            return pyo.Constraint.Skip
        return (sum(m.f[k, i, v] for i in range(n) if i != v)
                - sum(m.f[k, v, j] for j in range(n) if j != v) == m.y[k, v])
    model.flow_con = pyo.Constraint(model.K, model.N, rule=flow_con)

    def f_cap(m, k, i, j):
        return m.f[k, i, j] <= n * m.x[k, i, j]
    model.f_cap = pyo.Constraint(model.K, model.A, rule=f_cap)

    def depot_flow(m, k):
        return (sum(m.f[k, depot, j] for j in range(n) if j != depot)
                == sum(m.y[k, v] for v in range(n) if v != depot))
    model.depot_flow = pyo.Constraint(model.K, rule=depot_flow)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}