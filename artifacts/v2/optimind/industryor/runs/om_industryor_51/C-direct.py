import gurobipy as gp
from gurobipy import GRB

def solve(params):
    harry_cost = params["harry_cost"]
    hermione_cost = params["hermione_cost"]
    ron_cost = params["ron_cost"]
    fred_cost = params["fred_cost"]
    george_cost = params["george_cost"]
    ginny_cost = params["ginny_cost"]
    max_children = params["max_children"]
    min_children = params["min_children"]

    model = gp.Model("zhang_family")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: 1 = take child, 0 = don't take
    harry = model.addVar(vtype=GRB.BINARY, name="harry")
    hermione = model.addVar(vtype=GRB.BINARY, name="hermione")
    ron = model.addVar(vtype=GRB.BINARY, name="ron")
    fred = model.addVar(vtype=GRB.BINARY, name="fred")
    george = model.addVar(vtype=GRB.BINARY, name="george")
    ginny = model.addVar(vtype=GRB.BINARY, name="ginny")

    # Objective: minimize total cost
    model.setObjective(
        harry_cost * harry
        + hermione_cost * hermione
        + ron_cost * ron
        + fred_cost * fred
        + george_cost * george
        + ginny_cost * ginny,
        GRB.MINIMIZE
    )

    # Ginny must be taken
    model.addConstr(ginny == 1, name="ginny_required")

    # At most max_children children
    model.addConstr(harry + hermione + ron + fred + george + ginny <= max_children, name="max_children")

    # At least min_children children
    model.addConstr(harry + hermione + ron + fred + george + ginny >= min_children, name="min_children")

    # If Harry is taken, Fred is not taken
    model.addConstr(harry + fred <= 1, name="harry_not_fred")

    # If Harry is taken, George is not taken
    model.addConstr(harry + george <= 1, name="harry_not_george")

    # If George is taken, Fred must be taken
    model.addConstr(george <= fred, name="george_requires_fred")

    # If George is taken, Hermione must be taken
    model.addConstr(george <= hermione, name="george_requires_hermione")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}