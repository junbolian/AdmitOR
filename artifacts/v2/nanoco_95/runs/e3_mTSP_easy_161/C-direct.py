import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_nodes"])          # 9 (nodes 0..8)
    num_vehicles = int(params["num_vehicles"])  # 2

    dist = {}
    for i in range(n):
        for j in range(n):
            dist[i, j] = float(params[f"distance_{i}_{j}"])

    customers = list(range(1, n))   # 1..8
    all_nodes = list(range(n))      # 0..8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[v, i, j] = 1 if vehicle v travels arc i -> j
    x = {}
    for v in range(num_vehicles):
        for i in all_nodes:
            for j in all_nodes:
                if i != j:
                    x[v, i, j] = model.addVar(vtype=GRB.BINARY,
                                               name=f"x_{v}_{i}_{j}")

    # u[v, i]: MTZ position for vehicle v at customer i
    # lb=0 so unvisited customers can take value 0 without conflict
    u = {}
    for v in range(num_vehicles):
        for i in customers:
            u[v, i] = model.addVar(lb=0.0, ub=float(len(customers)),
                                   vtype=GRB.CONTINUOUS,
                                   name=f"u_{v}_{i}")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[v, i, j]
                    for v in range(num_vehicles)
                    for i in all_nodes
                    for j in all_nodes if i != j),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for j in customers:
        model.addConstr(
            gp.quicksum(x[v, i, j]
                        for v in range(num_vehicles)
                        for i in all_nodes if i != j) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation at each customer for each vehicle
    for v in range(num_vehicles):
        for k in customers:
            model.addConstr(
                gp.quicksum(x[v, i, k] for i in all_nodes if i != k) ==
                gp.quicksum(x[v, k, j] for j in all_nodes if j != k),
                name=f"flow_{v}_{k}"
            )

    # Each vehicle departs and returns to depot exactly once
    # (all customers must be served, so every vehicle must run a route)
    for v in range(num_vehicles):
        model.addConstr(
            gp.quicksum(x[v, 0, j] for j in customers) == 1,
            name=f"depart_{v}"
        )
        model.addConstr(
            gp.quicksum(x[v, i, 0] for i in customers) == 1,
            name=f"return_{v}"
        )

    # MTZ subtour elimination among customers for each vehicle
    # u[v,i] - u[v,j] + M * x[v,i,j] <= M - 1  for all v, i!=j in customers
    big_m = float(len(customers))
    for v in range(num_vehicles):
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[v, i] - u[v, j] + big_m * x[v, i, j] <= big_m - 1,
                        name=f"mtz_{v}_{i}_{j}"
                    )

    # Tighten: when vehicle v visits customer j, position must be >= 1
    # When not visited by v, x[v,i,j]=0 for all i, so MTZ is slack and u can be 0.
    for v in range(num_vehicles):
        for j in customers:
            in_flow = gp.quicksum(x[v, i, j] for i in all_nodes if i != j)
            # u[v,j] >= in_flow  (if visited, position >= 1)
            model.addConstr(u[v, j] >= in_flow, name=f"u_lb_{v}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}