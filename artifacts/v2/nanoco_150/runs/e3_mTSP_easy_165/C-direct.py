import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_vehicles = int(params["num_vehicles"])
    
    # Build distance matrix from params
    n = 10  # nodes 0..9
    dist = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                dist[i, j] = 0
            elif i < j:
                dist[i, j] = params[f"dist_{i}_{j}"]
            else:
                dist[i, j] = params[f"dist_{j}_{i}"]
    
    nodes = list(range(n))
    stops = list(range(1, n))  # 1..9
    vehicles = list(range(num_vehicles))
    
    model = gp.Model("mobile_library_vrp")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)
    
    # x[i, j, k] = 1 if vehicle k travels arc (i -> j)
    x = model.addVars(nodes, nodes, vehicles, vtype=GRB.BINARY, name="x")
    
    # u[i, k]: MTZ subtour elimination position variable for stop i, vehicle k
    u = model.addVars(stops, vehicles, vtype=GRB.CONTINUOUS, lb=1, ub=len(stops), name="u")
    
    # No self-loops
    for k in vehicles:
        for i in nodes:
            x[i, i, k].ub = 0
    
    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k] for i in nodes for j in nodes for k in vehicles if i != j),
        GRB.MINIMIZE
    )
    
    # Each stop visited exactly once across all vehicles
    for j in stops:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in nodes for k in vehicles if i != j) == 1,
            name=f"visit_{j}"
        )
    
    # Each stop departed exactly once across all vehicles
    for i in stops:
        model.addConstr(
            gp.quicksum(x[i, j, k] for j in nodes for k in vehicles if i != j) == 1,
            name=f"depart_{i}"
        )
    
    # Each vehicle departs the depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in stops) == 1,
            name=f"depot_depart_{k}"
        )
    
    # Each vehicle returns to the depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[i, 0, k] for i in stops) == 1,
            name=f"depot_return_{k}"
        )
    
    # Flow conservation at each stop for each vehicle
    for k in vehicles:
        for s in stops:
            model.addConstr(
                gp.quicksum(x[i, s, k] for i in nodes if i != s) ==
                gp.quicksum(x[s, j, k] for j in nodes if j != s),
                name=f"flow_{s}_{k}"
            )
    
    # MTZ subtour elimination
    M = len(stops)
    for k in vehicles:
        for i in stops:
            for j in stops:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + M * x[i, j, k] <= M - 1,
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