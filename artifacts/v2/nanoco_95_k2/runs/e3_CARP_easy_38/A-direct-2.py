import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["vehicle_capacity"]
    demands = params["demands"]
    K = int(params["num_vehicles"])
    R = int(params["num_service_segments"])
    dist = params["distance_matrix"]

    # Required service segments (order as given in demands)
    tasks = [(0, 3), (0, 4), (2, 3), (3, 4)]

    model = pyo.ConcreteModel()

    model.K = pyo.RangeSet(0, K - 1)
    model.R = pyo.RangeSet(0, R - 1)

    # x[k,r] = vehicle k serves task r
    model.x = pyo.Var(model.K, model.R, domain=pyo.Binary)
    # u[k,r] = task r is first task of vehicle k
    model.u = pyo.Var(model.K, model.R, domain=pyo.Binary)
    # v[k,r] = task r is last task of vehicle k
    model.v = pyo.Var(model.K, model.R, domain=pyo.Binary)
    # y[k,r,s] = vehicle k goes directly from task r to task s
    model.y = pyo.Var(model.K, model.R, model.R, domain=pyo.Binary)
    # o[k,r] = orientation: 0 -> (a0->a1), 1 -> (a1->a0)
    model.o = pyo.Var(model.K, model.R, domain=pyo.Binary)
    # z[k] = vehicle k used
    model.z = pyo.Var(model.K, domain=pyo.Binary)
    # order for MTZ subtour elimination
    model.t = pyo.Var(model.K, model.R, bounds=(0, R))

    a0 = [tasks[r][0] for r in range(R)]
    a1 = [tasks[r][1] for r in range(R)]

    def service_cost(r):
        return dist[a0[r]][a1[r]]

    def depart_cost(k, r):
        return dist[0][a0[r]] * (1 - model.o[k, r]) + dist[0][a1[r]] * model.o[k, r]

    def return_cost(k, r):
        return dist[a1[r]][0] * (1 - model.o[k, r]) + dist[a0[r]][0] * model.o[k, r]

    def trans_cost(k, r, s):
        d00 = dist[a1[r]][a0[s]]
        d01 = dist[a1[r]][a1[s]]
        d10 = dist[a0[r]][a0[s]]
        d11 = dist[a0[r]][a1[s]]
        orv = model.o[k, r]
        osv = model.o[k, s]
        return (
            d00 * (1 - orv) * (1 - osv)
            + d01 * (1 - orv) * osv
            + d10 * orv * (1 - osv)
            + d11 * orv * osv
        )

    def obj_rule(m):
        total = 0
        for k in m.K:
            for r in m.R:
                total += service_cost(r) * m.x[k, r]
                total += depart_cost(k, r) * m.u[k, r]
                total += return_cost(k, r) * m.v[k, r]
                for s in m.R:
                    if s != r:
                        total += trans_cost(k, r, s) * m.y[k, r, s]
        return total

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, r):
        return sum(m.x[k, r] for k in m.K) == 1

    model.cover = pyo.Constraint(model.R, rule=cover_rule)

    def cap_rule(m, k):
        return sum(demands[r] * m.x[k, r] for r in m.R) <= capacity

    model.cap = pyo.Constraint(model.K, rule=cap_rule)

    def u_link_rule(m, k, r):
        return m.u[k, r] <= m.x[k, r]

    model.u_link = pyo.Constraint(model.K, model.R, rule=u_link_rule)

    def v_link_rule(m, k, r):
        return m.v[k, r] <= m.x[k, r]

    model.v_link = pyo.Constraint(model.K, model.R, rule=v_link_rule)

    def y_link1_rule(m, k, r, s):
        if r == s:
            return pyo.Constraint.Skip
        return m.y[k, r, s] <= m.x[k, r]

    model.y_link1 = pyo.Constraint(model.K, model.R, model.R, rule=y_link1_rule)

    def y_link2_rule(m, k, r, s):
        if r == s:
            return pyo.Constraint.Skip
        return m.y[k, r, s] <= m.x[k, s]

    model.y_link2 = pyo.Constraint(model.K, model.R, model.R, rule=y_link2_rule)

    def flow_rule(m, k, r):
        outflow = sum(m.y[k, r, s] for s in m.R if s != r)
        inflow = sum(m.y[k, s, r] for s in m.R if s != r)
        return inflow + m.u[k, r] - outflow - m.v[k, r] == 0

    model.flow = pyo.Constraint(model.K, model.R, rule=flow_rule)

    def z_link_rule(m, k, r):
        return m.z[k] >= m.x[k, r]

    model.z_link = pyo.Constraint(model.K, model.R, rule=z_link_rule)

    def start_rule(m, k):
        return sum(m.u[k, r] for r in m.R) == m.z[k]

    model.start = pyo.Constraint(model.K, rule=start_rule)

    def end_rule(m, k):
        return sum(m.v[k, r] for r in m.R) == m.z[k]

    model.end = pyo.Constraint(model.K, rule=end_rule)

    M = R

    def mtz_rule(m, k, r, s):
        if r == s:
            return pyo.Constraint.Skip
        return m.t[k, s] >= m.t[k, r] + 1 - M * (1 - m.y[k, r, s]) - M * (1 - m.x[k, r])

    model.mtz = pyo.Constraint(model.K, model.R, model.R, rule=mtz_rule)

    def t_lo_rule(m, k, r):
        return m.t[k, r] >= 1 - M * (1 - m.x[k, r])

    model.t_lo = pyo.Constraint(model.K, model.R, rule=t_lo_rule)

    def t_hi_rule(m, k, r):
        return m.t[k, r] <= R

    model.t_hi = pyo.Constraint(model.K, model.R, rule=t_hi_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}