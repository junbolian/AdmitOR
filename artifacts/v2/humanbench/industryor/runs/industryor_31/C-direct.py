import gurobipy as gp
from gurobipy import GRB

def solve(params):
    car_lengths = params["car_lengths"]
    side_capacity = params["side_capacity"]

    # Support both list and dict for car_lengths
    if isinstance(car_lengths, dict):
        car_items = sorted(car_lengths.items())
        length_list = [v for _, v in car_items]
    else:
        length_list = list(car_lengths)

    n = len(length_list)
    cars = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if car i is assigned to side A, 0 if assigned to side B
    x = model.addVars(cars, vtype=GRB.BINARY, name="x")

    # Total length on each side
    L_A = model.addVar(lb=0.0, name="L_A")
    L_B = model.addVar(lb=0.0, name="L_B")

    # Auxiliary variable for the maximum (the street frontage to minimize)
    total = model.addVar(lb=0.0, name="total")

    # Define L_A and L_B
    model.addConstr(
        L_A == gp.quicksum(length_list[i] * x[i] for i in cars),
        name="def_LA"
    )
    model.addConstr(
        L_B == gp.quicksum(length_list[i] * (1 - x[i]) for i in cars),
        name="def_LB"
    )

    # Side capacity constraints (only binding if side_capacity is tight)
    model.addConstr(L_A <= side_capacity, name="cap_A")
    model.addConstr(L_B <= side_capacity, name="cap_B")

    # total = max(L_A, L_B): minimize the longer side (street frontage)
    model.addConstr(total >= L_A, name="total_geq_LA")
    model.addConstr(total >= L_B, name="total_geq_LB")

    model.setObjective(total, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}