import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vault_x = params["vault_x"]
    vault_y = params["vault_y"]
    atm_x = params["atm_x"]
    atm_y = params["atm_y"]
    tt0 = params["travel_time_0_to_atm"]
    tt1 = params["travel_time_atm1_to_atm"]
    tt2 = params["travel_time_atm2_to_atm"]
    tt3 = params["travel_time_atm3_to_atm"]
    tt4 = params["travel_time_atm4_to_atm"]
    tt5 = params["travel_time_atm5_to_atm"]
    tt6 = params["travel_time_atm6_to_atm7"]
    vault_ws = params["vault_window_start"]
    vault_we = params["vault_window_end"]
    atm_ws = params["atm_window_start"]
    atm_we = params["atm_window_end"]
    horizon = params["horizon"]

    n_atms = 7
    nodes = list(range(0, n_atms + 1))

    travel = {}
    for j in range(n_atms):
        node_j = j + 1
        travel[(0, node_j)] = tt0[j]
        travel[(node_j, 0)] = tt0[j]
    for jj in range(len(tt1)):
        node_j = jj + 2
        travel[(1, node_j)] = tt1[jj]
        travel[(node_j, 1)] = tt1[jj]
    for jj in range(len(tt2)):
        node_j = jj + 3
        travel[(2, node_j)] = tt2[jj]
        travel[(node_j, 2)] = tt2[jj]
    for jj in range(len(tt3)):
        node_j = jj + 4
        travel[(3, node_j)] = tt3[jj]
        travel[(node_j, 3)] = tt3[jj]
    for jj in range(len(tt4)):
        node_j = jj + 5
        travel[(4, node_j)] = tt4[jj]
        travel[(node_j, 4)] = tt4[jj]
    for jj in range(len(tt5)):
        node_j = jj + 6
        travel[(5, node_j)] = tt5[jj]
        travel[(node_j, 5)] = tt5[jj]
    travel[(6, 7)] = tt6
    travel[(7, 6)] = tt6
    for i in nodes:
        travel[(i, i)] = 0

    start = {}
    end = {}
    start[0] = vault_ws
    end[0] = vault_we
    for j in range(n_atms):
        node_j = j + 1
        start[node_j] = atm_ws[j]
        end[node_j] = atm_we[j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.atms = pyo.Set(initialize=range(1, n_atms + 1))

    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.t = pyo.Var(model.nodes, domain=pyo.NonNegativeReals)
    model.u = pyo.Var(model.atms, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(travel[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_in_rule(m, j):
        return sum(m.x[(i, j)] for i in m.nodes if i != j) == 1

    model.assign_in = pyo.Constraint(model.atms, rule=assign_in_rule)

    def assign_out_rule(m, i):
        return sum(m.x[(i, j)] for j in m.nodes if j != i) == 1

    model.assign_out = pyo.Constraint(model.atms, rule=assign_out_rule)

    def depot_out_rule(m):
        return sum(m.x[(0, j)] for j in m.atms) == 1

    model.depot_out = pyo.Constraint(rule=depot_out_rule)

    def depot_in_rule(m):
        return sum(m.x[(i, 0)] for i in m.atms) == 1

    model.depot_in = pyo.Constraint(rule=depot_in_rule)

    model.time_lb = pyo.Constraint(
        model.nodes, rule=lambda m, i: m.t[i] >= start[i]
    )
    model.time_ub = pyo.Constraint(
        model.nodes, rule=lambda m, i: m.t[i] <= end[i]
    )

    model.u_lb = pyo.Constraint(
        model.atms, rule=lambda m, i: m.u[i] >= 1
    )
    model.u_ub = pyo.Constraint(
        model.atms, rule=lambda m, i: m.u[i] <= n_atms
    )

    big_m = horizon + max(max(travel.values()), max(end.values()))

    def time_link_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.t[j] >= m.t[i] + travel[(i, j)] - big_m * (1 - m.x[(i, j)])

    model.time_link = pyo.Constraint(model.arcs, rule=time_link_rule)

    def mt_arc_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[j] >= m.u[i] + 1 - n_atms * (1 - m.x[(i, j)])

    model.mt_arc = pyo.Constraint(model.arcs, rule=mt_arc_rule)

    def horizon_arc_rule(m, i, j):
        if j != 0:
            return pyo.Constraint.Skip
        return m.t[i] + travel[(i, 0)] <= horizon

    model.horizon_arc = pyo.Constraint(model.arcs, rule=horizon_arc_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}