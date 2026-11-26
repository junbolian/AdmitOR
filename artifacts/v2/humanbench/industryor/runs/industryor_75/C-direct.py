import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]                      # list of 4: [robot, car, blocks, doll]
    plastic_avail = params["plastic_avail"]
    electronics_avail = params["electronics_avail"]
    plastic_req = params["plastic_req"]            # list of 4
    electronics_req = params["electronics_req"]    # list of 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Continuous production quantities
    x = model.addVars(4, lb=0.0, name="x")  # 0=robot, 1=car, 2=blocks, 3=doll

    # Binary indicators: y[i] = 1 if toy i is manufactured (x[i] > 0)
    y = model.addVars(4, vtype=GRB.BINARY, name="y")

    # Big-M upper bounds based on binding constraints
    # Max robot: min(plastic_avail/plastic_req[0], electronics_avail/electronics_req[0])
    M = [0.0] * 4
    for i in range(4):
        bounds = []
        if plastic_req[i] > 0:
            bounds.append(plastic_avail / plastic_req[i])
        if electronics_req[i] > 0:
            bounds.append(electronics_avail / electronics_req[i])
        M[i] = max(bounds) if bounds else 1e6

    # Link x[i] and y[i]: x[i] <= M[i] * y[i]
    for i in range(4):
        model.addConstr(x[i] <= M[i] * y[i], name=f"link_upper_{i}")

    # Resource constraints
    model.addConstr(
        gp.quicksum(plastic_req[i] * x[i] for i in range(4)) <= plastic_avail,
        name="plastic"
    )
    model.addConstr(
        gp.quicksum(electronics_req[i] * x[i] for i in range(4)) <= electronics_avail,
        name="electronics"
    )

    # If robots manufactured (y[0]=1) then no dolls (y[3]=0): y[0] + y[3] <= 1
    model.addConstr(y[0] + y[3] <= 1, name="robot_no_doll")

    # If model cars manufactured (y[1]=1) then building blocks manufactured (y[2]=1):
    # y[1] <= y[2]  (if y[1]=1 then y[2] must be 1; y[2] can be 1 without y[1])
    model.addConstr(y[1] <= y[2], name="car_implies_blocks")

    # Dolls cannot exceed model cars: x[3] <= x[1]
    model.addConstr(x[3] <= x[1], name="doll_le_car")

    # Objective: maximize profit
    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(4)),
        GRB.MAXIMIZE
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