import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = 8
    num_cars = 8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: maximize total assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i in range(num_participants) for j in range(num_cars)),
        GRB.MAXIMIZE
    )

    # Preference constraint: only assign if interested
    for i in range(num_participants):
        for j in range(num_cars):
            model.addConstr(x[i, j] <= preference_matrix[i][j], name=f"pref_{i}_{j}")

    # Participant capacity: each participant assigned to at most participant_capacity[i] cars
    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= participant_capacity[i],
            name=f"pcap_{i}"
        )

    # Car capacity: each car assigned to at most car_capacity[j] participants
    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= car_capacity[j],
            name=f"ccap_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}