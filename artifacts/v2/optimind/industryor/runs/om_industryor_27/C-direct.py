import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_D1 = params["demand_Donghai_1"]
    demand_D2 = params["demand_Donghai_2"]
    demand_D3 = params["demand_Donghai_3"]
    demand_N1 = params["demand_Nanjiang_1"]
    demand_N2 = params["demand_Nanjiang_2"]
    demand_N3 = params["demand_Nanjiang_3"]
    count1 = params["count_type_1"]
    count2 = params["count_type_2"]
    count3 = params["count_type_3"]
    count4 = params["count_type_4"]
    count5 = params["count_type_5"]
    count6 = params["count_type_6"]
    p2_target = params["p2_target"]
    p3_target = params["p3_target"]

    # Assignments: x[type, city, specialty], city: D=0, N=1, specialty: 1,2,3
    # Feasible (type, city, spec): type1->D1,D2,N1,N2; type2->D2,D3,N2,N3
    # type3->D1,D3,N1,N3; type4->D1,D3,N1,N3; type5->D2,D3,N2,N3; type6->D3,N3
    feasible = {
        1: [('D',1),('D',2),('N',1),('N',2)],
        2: [('D',2),('D',3),('N',2),('N',3)],
        3: [('D',1),('D',3),('N',1),('N',3)],
        4: [('D',1),('D',3),('N',1),('N',3)],
        5: [('D',2),('D',3),('N',2),('N',3)],
        6: [('D',3),('N',3)],
    }
    preferred_spec = {1:1, 2:2, 3:1, 4:3, 5:3, 6:3}
    preferred_city = {1:'D', 2:'D', 3:'N', 4:'N', 5:'D', 6:'N'}
    counts = {1:count1, 2:count2, 3:count3, 4:count4, 5:count5, 6:count6}

    model = gp.Model("recruitment")
    model.setParam("OutputFlag", 0)

    x = {}
    for t, assignments in feasible.items():
        for (c, s) in assignments:
            x[t, c, s] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{t}_{c}_{s}")

    # Deviation variables for P1 (under-supply of each city-specialty)
    d1_neg = {}
    demands = {('D',1):demand_D1,('D',2):demand_D2,('D',3):demand_D3,
               ('N',1):demand_N1,('N',2):demand_N2,('N',3):demand_N3}
    for (c, s) in demands:
        d1_neg[c, s] = model.addVar(lb=0, name=f"d1neg_{c}_{s}")

    # Deviation for P2 (preferred specialty count >= p2_target)
    d2_neg = model.addVar(lb=0, name="d2_neg")
    # Deviation for P3 (preferred city count >= p3_target)
    d3_neg = model.addVar(lb=0, name="d3_neg")

    # Supply constraints with deviations (P1: meet demand)
    for (c, s), dem in demands.items():
        supply = gp.quicksum(x[t, c, s] for t in feasible if (c, s) in feasible[t])
        model.addConstr(supply + d1_neg[c, s] >= dem, name=f"demand_{c}_{s}")

    # Capacity constraints
    for t in feasible:
        model.addConstr(
            gp.quicksum(x[t, c, s] for (c, s) in feasible[t]) <= counts[t],
            name=f"cap_{t}"
        )

    # P2: preferred specialty assignments
    pref_spec_expr = gp.quicksum(
        x[t, c, s]
        for t in feasible
        for (c, s) in feasible[t]
        if s == preferred_spec[t]
    )
    model.addConstr(pref_spec_expr + d2_neg >= p2_target, name="p2_constr")

    # P3: preferred city assignments
    pref_city_expr = gp.quicksum(
        x[t, c, s]
        for t in feasible
        for (c, s) in feasible[t]
        if c == preferred_city[t]
    )
    model.addConstr(pref_city_expr + d3_neg >= p3_target, name="p3_constr")

    # Preemptive goal programming: solve in priority order
    # P1: minimize sum of under-deviations for demand
    BigM = 1e9

    # Phase 1: minimize P1 deviations
    model.setObjective(gp.quicksum(d1_neg[c, s] for (c, s) in demands), GRB.MINIMIZE)
    model.optimize()
    if model.status != GRB.OPTIMAL:
        return {"objective": None, "status": "infeasible_p1"}
    p1_opt = model.ObjVal
    model.addConstr(gp.quicksum(d1_neg[c, s] for (c, s) in demands) <= p1_opt + 1e-6, name="p1_lock")

    # Phase 2: minimize P2 deviation
    model.setObjective(d2_neg, GRB.MINIMIZE)
    model.optimize()
    if model.status != GRB.OPTIMAL:
        return {"objective": None, "status": "infeasible_p2"}
    p2_opt = model.ObjVal
    model.addConstr(d2_neg <= p2_opt + 1e-6, name="p2_lock")

    # Phase 3: minimize P3 deviation
    model.setObjective(d3_neg, GRB.MINIMIZE)
    model.optimize()
    if model.status != GRB.OPTIMAL:
        return {"objective": None, "status": "infeasible_p3"}
    p3_opt = model.ObjVal
    model.addConstr(d3_neg <= p3_opt + 1e-6, name="p3_lock")

    # Final: minimize people not in preferred city (moved)
    non_pref_city_expr = gp.quicksum(
        x[t, c, s]
        for t in feasible
        for (c, s) in feasible[t]
        if c != preferred_city[t]
    )
    model.setObjective(non_pref_city_expr, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}