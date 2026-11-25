import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    
    n_nodes = 9  # 0=hub, 1-8=customers
    customers = list(range(1, 8 + 1))
    nodes = list(range(n_nodes))
    vehicles = list(range(num_vehicles))
    
    # dist[i][j] from params
    dist = distance_matrix
    
    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)
    
    # x[v,i,j] = 1 if vehicle v travels from i to j
    x = {}
    for v in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    x[v, i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{v}_{i}_{j}")
    
    # u[v,i] = position of node i in route of vehicle v (for MTZ subtour elimination), customers only
    u = {}
    for v in vehicles:
        for i in customers:
            u[v, i] = model.addVar(lb=1, ub=len(customers), vtype=GRB.CONTINUOUS, name=f"u_{v}_{i}")
    
    model.update()
    
    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[v, i, j]
                    for v in vehicles for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )
    
    # Each customer visited exactly once across all vehicles
    for c in customers:
        model.addConstr(
            gp.quicksum(x[v, i, c] for v in vehicles for i in nodes if i != c) == 1,
            name=f"visit_{c}"
        )
    
    # Flow conservation: if vehicle v enters node i, it must leave node i
    for v in vehicles:
        for i in nodes:
            model.addConstr(
                gp.quicksum(x[v, i, j] for j in nodes if j != i) ==
                gp.quicksum(x[v, j, i] for j in nodes if j != i),
                name=f"flow_{v}_{i}"
            )
    
    # Each vehicle departs hub at most once
    for v in vehicles:
        model.addConstr(
            gp.quicksum(x[v, 0, j] for j in customers) <= 1,
            name=f"depart_{v}"
        )
    
    # Each vehicle arrives at hub at most once
    for v in vehicles:
        model.addConstr(
            gp.quicksum(x[v, j, 0] for j in customers) <= 1,
            name=f"arrive_{v}"
        )
    
    # MTZ subtour elimination constraints (customers only)
    for v in vehicles:
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[v, i] - u[v, j] + len(customers) * x[v, i, j] <= len(customers) - 1,
                        name=f"mtz_{v}_{i}_{j}"
                    )
    
    # Link u to x: if vehicle v visits customer j (arrives from some node), u is bounded
    # Ensure u[v,i] is only meaningful if vehicle v visits i
    for v in vehicles:
        for i in customers:
            model.addConstr(
                u[v, i] >= gp.quicksum(x[v, j, i] for j in nodes if j != i),
                name=f"u_lb_{v}_{i}"
            )
    
    model.optimize()
    
    status = model.Status
    
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj_val = model.ObjVal
        result_status = "optimal" if status == GRB.OPTIMAL else "time_limit_feasible"
        return {"objective": float(obj_val), "status": "optimal" if status == GRB.OPTIMAL else result_status}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}