import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_robot = params["profit_per_robot"]
    profit_per_car = params["profit_per_car"]
    profit_per_blocks = params["profit_per_blocks"]
    profit_per_doll = params["profit_per_doll"]
    plastic_capacity = params["plastic_capacity"]
    electronics_capacity = params["electronics_capacity"]
    plastic_per_robot = params["plastic_per_robot"]
    plastic_per_car = params["plastic_per_car"]
    plastic_per_blocks = params["plastic_per_blocks"]
    plastic_per_doll = params["plastic_per_doll"]
    electronics_per_robot = params["electronics_per_robot"]
    electronics_per_car = params["electronics_per_car"]
    electronics_per_blocks = params["electronics_per_blocks"]
    electronics_per_doll = params["electronics_per_doll"]

    model = gp.Model("bright_future_toys")
    model.setParam("OutputFlag", 0)

    # Continuous production quantities
    x_robot = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_robot")
    x_car = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_car")
    x_blocks = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_blocks")
    x_doll = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_doll")

    # Binary indicators: y_i = 1 if toy type i is manufactured
    y_robot = model.addVar(vtype=GRB.BINARY, name="y_robot")
    y_car = model.addVar(vtype=GRB.BINARY, name="y_car")
    y_blocks = model.addVar(vtype=GRB.BINARY, name="y_blocks")
    y_doll = model.addVar(vtype=GRB.BINARY, name="y_doll")

    # Big-M: upper bounds on quantities from resource constraints
    # Maximum any single product can be produced is bounded by min of capacity/requirement
    M_robot = plastic_capacity / plastic_per_robot if plastic_per_robot > 0 else plastic_capacity
    M_car = plastic_capacity / plastic_per_car if plastic_per_car > 0 else plastic_capacity
    M_blocks = plastic_capacity / plastic_per_blocks if plastic_per_blocks > 0 else plastic_capacity
    M_doll = plastic_capacity / plastic_per_doll if plastic_per_doll > 0 else plastic_capacity

    # Link quantities to binary indicators
    model.addConstr(x_robot <= M_robot * y_robot, name="link_robot")
    model.addConstr(x_car <= M_car * y_car, name="link_car")
    model.addConstr(x_blocks <= M_blocks * y_blocks, name="link_blocks")
    model.addConstr(x_doll <= M_doll * y_doll, name="link_doll")

    # Force binary to 1 if quantity > 0 (using small epsilon via constraint):
    # If y=0 then x=0; if x>0 then y=1. The upper bound constraint handles this.
    # We also need: if y=1, x can be > 0 (no lower bound forcing production when y=1,
    # since the problem says "if they manufacture robots, they will not manufacture dolls"
    # meaning if robots are chosen, dolls are excluded — not that they must produce robots).

    # Resource constraints
    model.addConstr(
        plastic_per_robot * x_robot + plastic_per_car * x_car +
        plastic_per_blocks * x_blocks + plastic_per_doll * x_doll <= plastic_capacity,
        name="plastic"
    )
    model.addConstr(
        electronics_per_robot * x_robot + electronics_per_car * x_car +
        electronics_per_blocks * x_blocks + electronics_per_doll * x_doll <= electronics_capacity,
        name="electronics"
    )

    # Logical constraint 1: If robots are manufactured, dolls are not.
    # y_robot = 1 => y_doll = 0, equivalently y_robot + y_doll <= 1
    model.addConstr(y_robot + y_doll <= 1, name="robot_excludes_doll")

    # Logical constraint 2: If model cars are manufactured, building blocks must also be manufactured.
    # y_car = 1 => y_blocks = 1, equivalently y_car <= y_blocks
    model.addConstr(y_car <= y_blocks, name="car_requires_blocks")

    # Logical constraint 3: Number of dolls cannot exceed number of model cars.
    model.addConstr(x_doll <= x_car, name="doll_le_car")

    # Objective: maximize profit
    model.setObjective(
        profit_per_robot * x_robot + profit_per_car * x_car +
        profit_per_blocks * x_blocks + profit_per_doll * x_doll,
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