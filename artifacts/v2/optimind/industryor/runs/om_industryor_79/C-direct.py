import gurobipy as gp
from gurobipy import GRB

def solve(params):
    car_lengths = params["car_lengths"]
    side_capacity_limit = params["side_capacity_limit"]

    n = len(car_lengths)
    cars = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if car i is on side A, 0 if on side B
    x = model.addVars(cars, vtype=GRB.BINARY, name="x")

    # L_A = total length on side A, L_B = total length on side B
    L_A = model.addVar(lb=0.0, name="L_A")
    L_B = model.addVar(lb=0.0, name="L_B")

    # Total street length occupied = max(L_A, L_B) is not linear,
    # but the problem asks to minimize total length occupied on the street.
    # The street occupied on each side is independent (both sides run in parallel),
    # so the total street LENGTH (linear meters of street) used is max(L_A, L_B).
    # We minimize max(L_A, L_B).
    Z = model.addVar(lb=0.0, name="Z")

    model.addConstr(
        L_A == gp.quicksum(car_lengths[i] * x[i] for i in cars),
        name="def_L_A"
    )
    model.addConstr(
        L_B == gp.quicksum(car_lengths[i] * (1 - x[i]) for i in cars),
        name="def_L_B"
    )

    # Z >= L_A and Z >= L_B  =>  Z = max(L_A, L_B)
    model.addConstr(Z >= L_A, name="z_geq_LA")
    model.addConstr(Z >= L_B, name="z_geq_LB")

    # Side capacity constraints
    model.addConstr(L_A <= side_capacity_limit, name="cap_A")
    model.addConstr(L_B <= side_capacity_limit, name="cap_B")

    model.setObjective(Z, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}