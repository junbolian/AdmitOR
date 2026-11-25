import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_participants = params["n_participants"]
    n_cars = params["n_cars"]
    car_capacity = params["car_capacity"]
    participant_capacity = params["participant_capacity"]
    objective_coefficient = params["objective_coefficient"]

    # Allowed assignments based on problem description:
    # Only participant_1 can be assigned to car_1 or car_2
    allowed = [(1, 1), (1, 2)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only for allowed pairs
    x = {}
    for (p, c) in allowed:
        x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    # Determine coefficient for each allowed pair
    # objective_coefficient may be a scalar, 1D list, or 2D list/matrix
    def get_coeff(p, c):
        coef = objective_coefficient
        # If it's a 2D structure (list of lists or similar)
        if hasattr(coef, '__getitem__'):
            try:
                val = coef[p]
                if hasattr(val, '__getitem__'):
                    return float(val[c])
                else:
                    return float(val)
            except (IndexError, KeyError, TypeError):
                return float(coef)
        else:
            return float(coef)

    # Objective: maximize total weighted assignments
    model.setObjective(
        gp.quicksum(get_coeff(p, c) * x[p, c] for (p, c) in allowed),
        GRB.MAXIMIZE
    )

    # Each participant assigned to at most participant_capacity cars
    for p in range(n_participants):
        pairs = [(pp, cc) for (pp, cc) in allowed if pp == p]
        if pairs:
            model.addConstr(
                gp.quicksum(x[pp, cc] for (pp, cc) in pairs) <= participant_capacity,
                name=f"participant_{p}_cap"
            )

    # Each car assigned to at most car_capacity participants
    for c in range(n_cars):
        pairs = [(pp, cc) for (pp, cc) in allowed if cc == c]
        if pairs:
            model.addConstr(
                gp.quicksum(x[pp, cc] for (pp, cc) in pairs) <= car_capacity,
                name=f"car_{c}_cap"
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
        return {"objective": None, "status": f"status_{status}"}