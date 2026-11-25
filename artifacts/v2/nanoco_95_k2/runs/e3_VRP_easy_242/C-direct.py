import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    # Build distance matrix from params
    n_clinics = 8
    nodes = list(range(n_clinics + 1))  # 0..8
    
    dist = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                dist[i, j] = 0.0
            elif i < j:
                dist[i, j] = float(params[f"dist_{i}_{j}"])
                dist[j, i] = dist[i, j]
            # j < i handled by symmetry above

    n_vehicles = 2
    vehicles = list(range(n_vehicles))
    clinics = list(range(1, n_clinics + 1))  # 1..8

    model = gp.Model()
    model.Params.OutputFlag = 0

    # x[i, j, k] = 1 if vehicle k travels arc (i -> j)
    x = {}
    for k in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    x[i, j, k] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{k}")

    # u[i, k]: MTZ position variable for clinic i on vehicle k (1..8)
    u = {}
    for k in vehicles:
        for i in clinics:
            u[i, k] = model.addVar(lb=1.0, ub=float(n_clinics), vtype=GRB.CONTINUOUS, name=f"u_{i}_{k}")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k] for k in vehicles for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each clinic visited exactly once across all vehicles
    for c in clinics:
        model.addConstr(
            gp.quicksum(x[i, c, k] for k in vehicles for i in nodes if i != c) == 1,
            name=f"visit_in_{c}"
        )
        model.addConstr(
            gp.quicksum(x[c, j, k] for k in vehicles for j in nodes if j != c) == 1,
            name=f"visit_out_{c}"
        )

    # Each vehicle departs depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in clinics) == 1,
            name=f"depot_out_{k}"
        )
        model.addConstr(
            gp.quicksum(x[i, 0, k] for i in clinics) == 1,
            name=f"depot_in_{k}"
        )

    # Flow conservation at each clinic for each vehicle
    for k in vehicles:
        for c in clinics:
            model.addConstr(
                gp.quicksum(x[i, c, k] for i in nodes if i != c) ==
                gp.quicksum(x[c, j, k] for j in nodes if j != c),
                name=f"flow_{c}_{k}"
            )

    # MTZ subtour elimination (only for arcs between clinics)
    big_M = float(n_clinics)
    for k in vehicles:
        for i in clinics:
            for j in clinics:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + big_M * x[i, j, k] <= big_M - 1,
                        name=f"mtz_{i}_{j}_{k}"
                    )

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