import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_value = params["preference_value"]

    num_participants = 7
    num_cars = 7

    # preference_value may be a flat list of length 49 or a 7x7 nested list.
    # Normalise to a callable pref(i, j) -> 0/1.
    if isinstance(preference_value, dict):
        def pref(i, j):
            return preference_value[(i, j)]
    elif hasattr(preference_value, '__len__') and not hasattr(preference_value[0], '__len__'):
        # flat sequence of length num_participants * num_cars
        def pref(i, j):
            return preference_value[i * num_cars + j]
    else:
        # nested list / list-of-lists
        def pref(i, j):
            return preference_value[i][j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(x[i, j] for i in range(num_participants) for j in range(num_cars)),
        GRB.MAXIMIZE
    )

    for i in range(num_participants):
        for j in range(num_cars):
            model.addConstr(x[i, j] <= pref(i, j), name=f"pref_{i}_{j}")

    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= 1,
            name=f"one_car_{i}"
        )

    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= 1,
            name=f"one_participant_{j}"
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