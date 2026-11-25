import gurobipy as gp
from gurobipy import GRB

def solve(params):
    hosp_x = params["hosp_x"]
    hosp_y = params["hosp_y"]
    n1_x = params["n1_x"];  n1_y = params["n1_y"]
    n2_x = params["n2_x"];  n2_y = params["n2_y"]
    n3_x = params["n3_x"];  n3_y = params["n3_y"]
    n4_x = params["n4_x"];  n4_y = params["n4_y"]
    n5_x = params["n5_x"];  n5_y = params["n5_y"]
    n6_x = params["n6_x"];  n6_y = params["n6_y"]
    n7_x = params["n7_x"];  n7_y = params["n7_y"]
    n8_x = params["n8_x"];  n8_y = params["n8_y"]
    num_vehicles = int(params["num_vehicles"])

    # Build distance dict from params (symmetric)
    raw_dist = {}
    pairs = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),
        (1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),
        (2,3),(2,4),(2,5),(2,6),(2,7),(2,8),
        (3,4),(3,5),(3,6),(3,7),(3,8),
        (4,5),(4,6),(4,7),(4,8),
        (5,6),(5,7),(5,8),
        (6,7),(6,8),
        (7,8),
    ]
    for (a, b) in pairs:
        key = f"dist_{a}_{b}"
        val = params[key]
        raw_dist[(a, b)] = val
        raw_dist[(b, a)] = val

    # Nodes: 0 = depot, 1..8 = clinics
    N = 9
    nodes = list(range(N))
    clinics = list(range(1, N))
    depot = 0
    K = num_vehicles  # number of vehicles

    # For the VRP with multiple depot copies, we use a standard 2-index formulation
    # with MTZ subtour elimination per vehicle.
    # We replicate the depot as node 0 for departures and returns.
    # Arc set: all (i,j) with i != j, i,j in nodes
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    dist = {(i, j): raw_dist[(i, j)] for (i, j) in arcs}

    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j,k] = 1 if vehicle k travels arc (i,j)
    x = model.addVars(
        [(i, j, k) for (i, j) in arcs for k in range(K)],
        vtype=GRB.BINARY, name="x"
    )

    # u[i,k] = position of node i in route of vehicle k (MTZ), for i in clinics
    u = model.addVars(
        [(i, k) for i in clinics for k in range(K)],
        lb=1.0, ub=float(len(clinics)), vtype=GRB.CONTINUOUS, name="u"
    )

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k]
                    for (i, j) in arcs for k in range(K)),
        GRB.MINIMIZE
    )

    # Each clinic visited exactly once across all vehicles
    for j in clinics:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in nodes if i != j for k in range(K)) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation at each clinic for each vehicle
    for k in range(K):
        for h in clinics:
            model.addConstr(
                gp.quicksum(x[i, h, k] for i in nodes if i != h) ==
                gp.quicksum(x[h, j, k] for j in nodes if j != h),
                name=f"flow_{h}_{k}"
            )

    # Each vehicle departs depot exactly once
    for k in range(K):
        model.addConstr(
            gp.quicksum(x[depot, j, k] for j in clinics) == 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to depot exactly once
    for k in range(K):
        model.addConstr(
            gp.quicksum(x[i, depot, k] for i in clinics) == 1,
            name=f"return_{k}"
        )

    # MTZ subtour elimination (only among clinics, per vehicle)
    M_mtz = len(clinics)
    for k in range(K):
        for i in clinics:
            for j in clinics:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + M_mtz * x[i, j, k] <= M_mtz - 1,
                        name=f"mtz_{i}_{j}_{k}"
                    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}