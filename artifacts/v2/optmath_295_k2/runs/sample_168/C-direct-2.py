import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    p0_4_interest = params["participant_0_4_interest"]
    p4_car1_interest = params["participant_4_car_1_interest"]
    p4_forbidden_interest = params["participant_4_forbidden_interest"]

    model = gp.Model("assignment")
    model.setParam('OutputFlag', 0)

    # Build interest matrix: interest[i, j] = 1 if participant i is interested in car j
    # Participants 0-3 share a single interest flag for all cars.
    # Participant 4 has a separate flag for car_1 vs. the other (forbidden) cars.
    interest = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if i < 4:
                interest[i, j] = 1 if p0_4_interest else 0
            elif j == 1:
                interest[i, j] = 1 if p4_car1_interest else 0
            else:
                interest[i, j] = 1 if p4_forbidden_interest else 0

    # Decision variables: x[i, j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if interest[i, j]:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Each participant assigned to at most one car
    for i in range(num_participants):
        terms = [x[i, j] for j in range(num_cars) if (i, j) in x]
        if terms:
            model.addConstr(gp.quicksum(terms) <= 1, name=f"participant_{i}")

    # Each car assigned to at most one participant
    for j in range(num_cars):
        terms = [x[i, j] for i in range(num_participants) if (i, j) in x]
        if terms:
            model.addConstr(gp.quicksum(terms) <= 1, name=f"car_{j}")

    # Objective: maximize total assignments
    all_terms = [x[i, j] for i in range(num_participants) for j in range(num_cars) if (i, j) in x]
    if all_terms:
        model.setObjective(gp.quicksum(all_terms), GRB.MAXIMIZE)
    else:
        model.setObjective(0, GRB.MAXIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}