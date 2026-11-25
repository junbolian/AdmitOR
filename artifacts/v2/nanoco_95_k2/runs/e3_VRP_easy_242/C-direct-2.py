import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    # Build distance matrix from params
    n_clinics = 8
    nodes = list(range(n_clinics + 1))  # 0..8
    n_vehicles = 2

    # Build symmetric distance dict
    dist = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                dist[i, j] = 0.0
            elif i < j:
                dist[i, j] = float(params[f"dist_{i}_{j}"])
                dist[j, i] = dist[i, j]
            # j < i handled by above

    clinics = list(range(1, n_clinics + 1))  # 1..8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[v, i, j] = 1 if vehicle v travels from node i to node j
    x = {}
    for v in range(n_vehicles):
        for i in nodes:
            for j in nodes:
                if i != j:
                    x[v, i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{v}_{i}_{j}")

    # u[v, i] = position of node i in vehicle v's route (for MTZ subtour elimination)
    # only for clinic nodes
    u = {}
    for v in range(n_vehicles):
        for i in clinics:
            u[v, i] = model.addVar(lb=1.0, ub=float(n_clinics), vtype=GRB.CONTINUOUS, name=f"u_{v}_{i}")

    model.update()

    # Objective: minimize total distance
    obj = gp.quicksum(
        dist[i, j] * x[v, i, j]
        for v in range(n_vehicles)
        for i in nodes
        for j in nodes
        if i != j
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraint 1: each clinic visited exactly once across all vehicles
    for c in clinics:
        model.addConstr(
            gp.quicksum(x[v, i, c] for v in range(n_vehicles) for i in nodes if i != c) == 1,
            name=f"visit_{c}"
        )

    # Constraint 2: flow conservation at each node for each vehicle
    for v in range(n_vehicles):
        for c in clinics:
            # inflow == outflow at each clinic
            model.addConstr(
                gp.quicksum(x[v, i, c] for i in nodes if i != c) ==
                gp.quicksum(x[v, c, j] for j in nodes if j != c),
                name=f"flow_{v}_{c}"
            )

    # Constraint 3: each vehicle departs depot exactly once
    for v in range(n_vehicles):
        model.addConstr(
            gp.quicksum(x[v, 0, j] for j in clinics) == 1,
            name=f"depot_out_{v}"
        )

    # Constraint 4: each vehicle returns to depot exactly once
    for v in range(n_vehicles):
        model.addConstr(
            gp.quicksum(x[v, i, 0] for i in clinics) == 1,
            name=f"depot_in_{v}"
        )

    # Constraint 5: MTZ subtour elimination (only among clinic nodes per vehicle)
    big_M = float(n_clinics)
    for v in range(n_vehicles):
        for i in clinics:
            for j in clinics:
                if i != j:
                    model.addConstr(
                        u[v, i] - u[v, j] + big_M * x[v, i, j] <= big_M - 1,
                        name=f"mtz_{v}_{i}_{j}"
                    )

    # Constraint 6: a vehicle can only visit a clinic if it is assigned to it
    # (implicit via visit constraint, but also bound x[v,i,j] for unused vehicles)
    # This is naturally handled: if clinic not on route, flow is zero.

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}