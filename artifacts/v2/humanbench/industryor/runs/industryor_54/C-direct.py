import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d_dh1 = params["demand_donghai_major1"]
    d_dh2 = params["demand_donghai_major2"]
    d_dh3 = params["demand_donghai_major3"]
    d_nj1 = params["demand_nanjiang_major1"]
    d_nj2 = params["demand_nanjiang_major2"]
    d_nj3 = params["demand_nanjiang_major3"]
    sz = [
        params["category1_size"],
        params["category2_size"],
        params["category3_size"],
        params["category4_size"],
        params["category5_size"],
        params["category6_size"],
    ]
    p2_goal = params["preferred_major_goal"]
    p3_goal = params["preferred_city_goal"]

    # Feasible assignments: (category_index 0-5, city 0=DH/1=NJ, major 1-3)
    # city: 0=Donghai, 1=Nanjiang
    assignments = [
        (0, 0, 1), (0, 0, 2), (0, 1, 1), (0, 1, 2),  # cat1
        (1, 0, 2), (1, 0, 3), (1, 1, 2), (1, 1, 3),  # cat2
        (2, 0, 1), (2, 0, 3), (2, 1, 1), (2, 1, 3),  # cat3
        (3, 0, 1), (3, 0, 3), (3, 1, 1), (3, 1, 3),  # cat4
        (4, 0, 2), (4, 0, 3), (4, 1, 2), (4, 1, 3),  # cat5
        (5, 0, 3), (5, 1, 3),                          # cat6
    ]

    # preferred major per category (1-indexed)
    pref_major = [1, 2, 1, 3, 3, 3]
    # preferred city per category: 0=DH, 1=NJ
    pref_city = [0, 0, 1, 1, 0, 1]

    M_p1 = 1e9
    M_p2 = 1e6
    M_p3 = 1e3

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: number assigned per (cat, city, major)
    x = {}
    for (c, ci, mj) in assignments:
        x[(c, ci, mj)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{c}_{ci}_{mj}")

    # Deviational variables for demand goals (p1) - 6 demand constraints
    # (city, major) -> demand
    demands = {(0,1): d_dh1, (0,2): d_dh2, (0,3): d_dh3,
               (1,1): d_nj1, (1,2): d_nj2, (1,3): d_nj3}

    n_demand = {}  # negative deviation (under-supply)
    p_demand = {}  # positive deviation (over-supply)
    for key in demands:
        n_demand[key] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"nd_{key[0]}_{key[1]}")
        p_demand[key] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"pd_{key[0]}_{key[1]}")

    # Demand constraints
    for (ci, mj), dem in demands.items():
        supply = gp.quicksum(x[(c, ci2, mj2)] for (c, ci2, mj2) in assignments if ci2 == ci and mj2 == mj)
        model.addConstr(supply - n_demand[(ci, mj)] + p_demand[(ci, mj)] == dem,
                        name=f"dem_{ci}_{mj}")

    # Category size constraints
    for c_idx in range(6):
        total = gp.quicksum(x[(c, ci, mj)] for (c, ci, mj) in assignments if c == c_idx)
        model.addConstr(total <= sz[c_idx], name=f"cat_size_{c_idx}")

    # p2: preferred major goal
    n2 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="n2")
    p2 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="p2_dev")
    pref_major_supply = gp.quicksum(
        x[(c, ci, mj)] for (c, ci, mj) in assignments if mj == pref_major[c]
    )
    model.addConstr(pref_major_supply - n2 + p2 == p2_goal, name="pref_major_constr")

    # p3: preferred city goal
    n3 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="n3")
    p3 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="p3_dev")
    pref_city_supply = gp.quicksum(
        x[(c, ci, mj)] for (c, ci, mj) in assignments if ci == pref_city[c]
    )
    model.addConstr(pref_city_supply - n3 + p3 == p3_goal, name="pref_city_constr")

    # Objective: preemptive weights
    # p1: minimize under-supply of demand (highest priority)
    p1_obj = gp.quicksum(n_demand[key] for key in demands)
    p2_obj = n2  # minimize under-achievement of preferred major goal
    p3_obj = n3  # minimize under-achievement of preferred city goal

    model.setObjective(M_p1 * p1_obj + M_p2 * p2_obj + M_p3 * p3_obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}