import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_Harry = params["cost_Harry"]
    cost_Hermione = params["cost_Hermione"]
    cost_Ron = params["cost_Ron"]
    cost_Fred = params["cost_Fred"]
    cost_George = params["cost_George"]
    cost_Ginny = params["cost_Ginny"]
    max_children = params["max_children"]
    min_children = params["min_children"]

    model = gp.Model("zhang_family_trip")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: 1 if child is taken
    Harry = model.addVar(vtype=GRB.BINARY, name="Harry")
    Hermione = model.addVar(vtype=GRB.BINARY, name="Hermione")
    Ron = model.addVar(vtype=GRB.BINARY, name="Ron")
    Fred = model.addVar(vtype=GRB.BINARY, name="Fred")
    George = model.addVar(vtype=GRB.BINARY, name="George")
    Ginny = model.addVar(vtype=GRB.BINARY, name="Ginny")

    # Objective: minimize total cost
    model.setObjective(
        cost_Harry * Harry +
        cost_Hermione * Hermione +
        cost_Ron * Ron +
        cost_Fred * Fred +
        cost_George * George +
        cost_Ginny * Ginny,
        GRB.MINIMIZE
    )

    # Ginny must be taken
    model.addConstr(Ginny == 1, name="ginny_required")

    # At most max_children children
    model.addConstr(Harry + Hermione + Ron + Fred + George + Ginny <= max_children, name="max_children_constr")

    # At least min_children children
    model.addConstr(Harry + Hermione + Ron + Fred + George + Ginny >= min_children, name="min_children_constr")

    # If Harry is taken, Fred is not taken
    model.addConstr(Harry + Fred <= 1, name="harry_not_fred")

    # If Harry is taken, George is not taken
    model.addConstr(Harry + George <= 1, name="harry_not_george")

    # If George is taken, Fred must be taken
    model.addConstr(George <= Fred, name="george_requires_fred")

    # If George is taken, Hermione must be taken
    model.addConstr(George <= Hermione, name="george_requires_hermione")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}