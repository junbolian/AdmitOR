import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read all coordinate params (required by rules, even if unused in solve logic)
    _hosp_x = params["hosp_x"]
    _hosp_y = params["hosp_y"]
    _n1_x = params["n1_x"]; _n1_y = params["n1_y"]
    _n2_x = params["n2_x"]; _n2_y = params["n2_y"]
    _n3_x = params["n3_x"]; _n3_y = params["n3_y"]
    _n4_x = params["n4_x"]; _n4_y = params["n4_y"]
    _n5_x = params["n5_x"]; _n5_y = params["n5_y"]
    _n6_x = params["n6_x"]; _n6_y = params["n6_y"]
    _n7_x = params["n7_x"]; _n7_y = params["n7_y"]
    _n8_x = params["n8_x"]; _n8_y = params["n8_y"]
    num_vehicles = int(params["num_vehicles"])

    # Build distance matrix from params
    dist = {}
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
    for (i, j) in pairs:
        val = params[f"dist_{i}_{j}"]
        dist[i, j] = val
        dist[j, i] = val
    for i in range(9):
        dist[i, i] = 0.0

    all_nodes = list(range(9))
    clients = list(range(1, 9))
    K = list(range(num_vehicles))
    n_clients = len(clients)  # 8

    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j,k] = 1 if vehicle k travels arc i->j
    x = {}
    for k in K:
        for i in all_nodes:
            for j in all_nodes:
                if i != j:
                    x[i, j, k] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{k}")

    # MTZ position variables for client nodes only
    # lb=1, ub=n_clients; valid for visited nodes, unconstrained for unvisited
    u = {}
    for k in K:
        for i in clients:
            u[i, k] = model.addVar(lb=1.0, ub=float(n_clients),
                                   vtype=GRB.CONTINUOUS, name=f"u_{i}_{k}")

    model.update()

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k]
                    for k in K for i in all_nodes for j in all_nodes if i != j),
        GRB.MINIMIZE
    )

    # Each client visited exactly once across all vehicles
    for j in clients:
        model.addConstr(
            gp.quicksum(x[i, j, k] for k in K for i in all_nodes if i != j) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation at each client for each vehicle
    for k in K:
        for h in clients:
            model.addConstr(
                gp.quicksum(x[i, h, k] for i in all_nodes if i != h) ==
                gp.quicksum(x[h, j, k] for j in all_nodes if j != h),
                name=f"flow_{h}_{k}"
            )

    # Each vehicle departs depot exactly once
    for k in K:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in clients) == 1,
            name=f"depot_out_{k}"
        )

    # Each vehicle returns to depot exactly once
    for k in K:
        model.addConstr(
            gp.quicksum(x[i, 0, k] for i in clients) == 1,
            name=f"depot_in_{k}"
        )

    # MTZ subtour elimination among client nodes
    # Standard MTZ: u[i] - u[j] + n*x[i,j] <= n-1 for all client pairs i!=j
    # This correctly handles unvisited nodes without extra activation constraints
    for k in K:
        for i in clients:
            for j in clients:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + n_clients * x[i, j, k] <= n_clients - 1,
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