import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 8
    vault_x = params["vault_x"]
    vault_y = params["vault_y"]
    atm_x = params["atm_x"]
    atm_y = params["atm_y"]
    t0 = params["travel_time_0_to_atm"]

    T = [[0]*n for _ in range(n)]
    for j in range(7):
        T[0][j+1] = t0[j]
        T[j+1][0] = t0[j]
    t1 = params["travel_time_atm1_to_atm"]
    for k in range(6):
        T[1][k+2] = t1[k]
        T[k+2][1] = t1[k]
    t2 = params["travel_time_atm2_to_atm"]
    for k in range(5):
        T[2][k+3] = t2[k]
        T[k+3][2] = t2[k]
    t3 = params["travel_time_atm3_to_atm"]
    for k in range(4):
        T[3][k+4] = t3[k]
        T[k+4][3] = t3[k]
    t4 = params["travel_time_atm4_to_atm"]
    for k in range(3):
        T[4][k+5] = t4[k]
        T[k+5][4] = t4[k]
    t5 = params["travel_time_atm5_to_atm"]
    for k in range(2):
        T[5][k+6] = t5[k]
        T[k+6][5] = t5[k]
    T[6][7] = params["travel_time_atm6_to_atm7"]
    T[7][6] = params["travel_time_atm6_to_atm7"]

    start = [0]*n
    end = [0]*n
    start[0] = params["vault_window_start"]
    end[0] = params["vault_window_end"]
    aws = params["atm_window_start"]
    awe = params["atm_window_end"]
    for j in range(7):
        start[j+1] = aws[j]
        end[j+1] = awe[j]

    horizon = params["horizon"]

    arcs = []
    for j in range(1, n):
        arcs.append((0, j))
    for i in range(1, n):
        for j in range(i+1, n):
            arcs.append((i, j))
    for i in range(1, n):
        arcs.append((i, 0))

    model = pyo.ConcreteModel()

    model.V = pyo.RangeSet(0, n-1)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # Arrival times at nodes 1..7; departure time from vault is fixed at 0
    model.t = pyo.Var(pyo.RangeSet(1, n-1), domain=pyo.NonNegativeReals,
                      bounds=(0, horizon))

    # Big-M
    Mval = horizon + max(T[i][j] for i in range(n) for j in range(n))
    model.Mval = pyo.Param(initialize=Mval, mutable=True)

    def obj_rule(m):
        return sum(T[i][j] * m.x[i, j] for (i, j) in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def in_rule(m, j):
        return sum(m.x[i, jj] for (i, jj) in m.A if jj == j) == 1
    model.in_con = pyo.Constraint(pyo.RangeSet(1, n-1), rule=in_rule)

    def out_rule(m, i):
        return sum(m.x[ii, j] for (ii, j) in m.A if ii == i) == 1
    model.out_con = pyo.Constraint(pyo.RangeSet(1, n-1), rule=out_rule)

    model.vault_out = pyo.Constraint(
        expr=sum(model.x[0, j] for (i, j) in model.A if i == 0) == 1)
    model.vault_in = pyo.Constraint(
        expr=sum(model.x[i, 0] for (i, j) in model.A if j == 0) == 1)

    # Time windows for ATMs
    def tw_rule(m, j):
        return pyo.inequality(start[j], m.t[j], end[j])
    model.tw = pyo.Constraint(pyo.RangeSet(1, n-1), rule=tw_rule)

    # Time propagation for arcs leaving vault: if x[0,j]=1, then t[j] >= T[0][j]
    def time_from_vault(m, j):
        return m.t[j] >= T[0][j] - m.Mval * (1 - m.x[0, j])
    model.time_from_vault = pyo.Constraint(pyo.RangeSet(1, n-1), rule=time_from_vault)

    # Time propagation for ATM->ATM arcs (i<j): t[j] >= t[i] + T[i][j] - M(1-x)
    def time_atm_to_atm(m, i, j):
        return m.t[j] >= m.t[i] + T[i][j] - m.Mval * (1 - m.x[i, j])
    atm_arc_pairs = [(i, j) for (i, j) in arcs if i >= 1 and j >= 1]
    model.AtmArcs = pyo.Set(initialize=atm_arc_pairs, dimen=2)
    model.time_atm_to_atm = pyo.Constraint(model.AtmArcs, rule=time_atm_to_atm)

    # Horizon: arrival back at vault must be <= horizon
    def return_horizon(m, i):
        return m.t[i] + T[i][0] <= horizon + m.Mval * (1 - m.x[i, 0])
    model.return_horizon = pyo.Constraint(pyo.RangeSet(1, n-1), rule=return_horizon)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}