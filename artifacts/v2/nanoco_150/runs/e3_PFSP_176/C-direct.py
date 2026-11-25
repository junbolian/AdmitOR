import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    processing_times = params["processing_times"]
    num_vehicles = params["num_vehicles"]
    num_workstations = params["num_workstations"]

    vehicles = list(range(num_vehicles))
    workstations = list(range(num_workstations))

    # p[i][j] = processing time of vehicle i at workstation j
    p = {(i, j): processing_times[i][j] for i in vehicles for j in workstations}

    # Permutation-based exact approach: enumerate all n! permutations and compute makespan
    # For n=4 this is 24 permutations — tractable without MIP.
    # We'll still use Gurobi as required, encoding via binary position assignment variables.

    # x[i][pos] = 1 if vehicle i is assigned to position pos
    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    # Binary assignment: x[i, pos]
    x = {}
    for i in vehicles:
        for pos in range(num_vehicles):
            x[i, pos] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{pos}")

    # C[pos, j] = completion time of vehicle in position pos at workstation j
    # We need an upper bound for big-M
    total_time = sum(p[i, j] for i in vehicles for j in workstations)
    BIG_M = total_time

    C = {}
    for pos in range(num_vehicles):
        for j in workstations:
            C[pos, j] = model.addVar(lb=0.0, ub=BIG_M, name=f"C_{pos}_{j}")

    makespan = model.addVar(lb=0.0, name="makespan")

    # Each vehicle assigned to exactly one position
    for i in vehicles:
        model.addConstr(gp.quicksum(x[i, pos] for pos in range(num_vehicles)) == 1)

    # Each position has exactly one vehicle
    for pos in range(num_vehicles):
        model.addConstr(gp.quicksum(x[i, pos] for i in vehicles) == 1)

    # Completion time constraints using big-M linearization
    # C[pos, j] >= sum_i p[i,j] * x[i,pos]  (processing must finish)
    # C[pos, j] >= C[pos-1, j] + sum_i p[i,j] * x[i,pos]  (same workstation, previous position)
    # C[pos, j] >= C[pos, j-1] + sum_i p[i,j] * x[i,pos]  (same vehicle, previous workstation)

    for pos in range(num_vehicles):
        proc_j = {}
        for j in workstations:
            proc_j[j] = gp.quicksum(p[i, j] * x[i, pos] for i in vehicles)

        for j in workstations:
            # Must be at least the processing time itself
            model.addConstr(C[pos, j] >= proc_j[j])

            # Previous position on same workstation
            if pos > 0:
                model.addConstr(C[pos, j] >= C[pos - 1, j] + proc_j[j])

            # Previous workstation for same position
            if j > 0:
                model.addConstr(C[pos, j] >= C[pos, j - 1] + proc_j[j])

    # Makespan = completion time of last position at last workstation
    last_ws = num_workstations - 1
    model.addConstr(makespan >= C[num_vehicles - 1, last_ws])

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}