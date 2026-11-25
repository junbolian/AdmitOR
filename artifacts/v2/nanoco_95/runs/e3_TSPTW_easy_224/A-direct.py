import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_atms = 7
    nodes = list(range(num_atms + 1))          # 0 = vault, 1..7 = ATMs
    atm_nodes = list(range(1, num_atms + 1))

    # ---- travel time matrix (symmetric) ----
    travel = {}
    for i in nodes:
        travel[(i, i)] = 0

    # vault -> ATMs
    v2a = list(params["vault_to_atm_times"])
    for k, j in enumerate(atm_nodes):
        travel[(0, j)] = v2a[k]
        travel[(j, 0)] = v2a[k]

    # ATM i -> higher-index ATMs
    for i in atm_nodes:
        if i <= 5:
            row = list(params["atm%d_to_atm_times" % i])
            higher = list(range(i + 1, num_atms + 1))
            for k, j in enumerate(higher):
                travel[(i, j)] = row[k]
                travel[(j, i)] = row[k]
        elif i == 6:
            t67 = params["atm6_to_atm7_time"]
            travel[(6, 7)] = t67
            travel[(7, 6)] = t67

    # ---- time windows ----
    tw_start = {0: params["vault_time_window_start"]}
    tw_end = {0: params["vault_time_window_end"]}
    for i in atm_nodes:
        tw_start[i] = params["atm%d_time_window_start" % i]
        tw_end[i] = params["atm%d_time_window_end" % i]

    horizon = params["horizon"]
    service = params["service_time"]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes, ordered=True)
    model.ATMS = pyo.Set(initialize=atm_nodes, ordered=True)

    def arc_init(m):
        return [(i, j) for i in nodes for j in nodes if i != j]

    model.ARCS = pyo.Set(dimen=2, initialize=arc_init)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.u = pyo.Var(model.NODES, domain=pyo.NonNegativeReals, bounds=(0, horizon))

    def obj_rule(m):
        return sum(travel[(i, j)] * m.x[(i, j)] for (i, j) in m.ARCS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in nodes if j != i) == 1

    model.out_deg = pyo.Constraint(model.NODES, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in nodes if i != j) == 1

    model.in_deg = pyo.Constraint(model.NODES, rule=in_rule)

    # arrival time at vault: within its window, and at least its start
    def vault_lb(m):
        return m.u[0] >= tw_start[0]

    def vault_ub(m):
        return m.u[0] <= tw_end[0]

    model.vault_lower = pyo.Constraint(rule=vault_lb)
    model.vault_upper = pyo.Constraint(rule=vault_ub)

    def tw_lb(m, i):
        return m.u[i] >= tw_start[i]

    def tw_ub(m, i):
        return m.u[i] <= tw_end[i]

    model.tw_lower = pyo.Constraint(model.ATMS, rule=tw_lb)
    model.tw_upper = pyo.Constraint(model.ATMS, rule=tw_ub)

    # return to vault within horizon
    model.return_horizon = pyo.Constraint(
        expr=model.u[0] <= horizon
    )

    big_m = horizon + max(tw_end.values()) + service + 1000

    def time_prop(m, i, j):
        if j == 0:
            return pyo.Constraint.Skip
        return m.u[j] >= m.u[i] + service + travel[(i, j)] - big_m * (1 - m.x[(i, j)])

    model.time_prop = pyo.Constraint(model.ARCS, rule=time_prop)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}