import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assignment_allowance = params["assignment_allowance"]
    participant_assignment_capacity = params["participant_assignment_capacity"]
    car_assignment_capacity = params["car_assignment_capacity"]

    # assignment_allowance is a list of lists (rows=participants, cols=cars)
    num_participants = len(assignment_allowance)
    num_cars = len(assignment_allowance[0])

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {
        (i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
        for i in participants
        for j in cars
    }

    model.setObjective(
        gp.quicksum(x[i, j] for i in participants for j in cars),
        GRB.MAXIMIZE
    )

    # Respect eligibility
    for i in participants:
        for j in cars:
            if assignment_allowance[i][j] == 0:
                model.addConstr(x[i, j] == 0)

    # Each participant assigned to at most their capacity
    for i in participants:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cars) <= participant_assignment_capacity[i]
        )

    # Each car assigned to at most its capacity
    for j in cars:
        model.addConstr(
            gp.quicksum(x[i, j] for i in participants) <= car_assignment_capacity[j]
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}