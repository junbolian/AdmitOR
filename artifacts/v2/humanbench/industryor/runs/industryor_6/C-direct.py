import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_alice = params["cost_alice"]
    cost_bob = params["cost_bob"]
    cost_charlie = params["cost_charlie"]
    cost_diana = params["cost_diana"]
    cost_ella = params["cost_ella"]
    max_children = params["max_children"]
    min_children = params["min_children"]

    model = gp.Model("lee_family")
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    alice = model.addVar(vtype=GRB.BINARY, name="alice")
    bob = model.addVar(vtype=GRB.BINARY, name="bob")
    charlie = model.addVar(vtype=GRB.BINARY, name="charlie")
    diana = model.addVar(vtype=GRB.BINARY, name="diana")
    ella = model.addVar(vtype=GRB.BINARY, name="ella")

    # Objective: minimize total cost
    model.setObjective(
        cost_alice * alice + cost_bob * bob + cost_charlie * charlie +
        cost_diana * diana + cost_ella * ella,
        GRB.MINIMIZE
    )

    # Constraint: at most max_children children
    model.addConstr(alice + bob + charlie + diana + ella <= max_children, "max_children")

    # Constraint: at least min_children children
    model.addConstr(alice + bob + charlie + diana + ella >= min_children, "min_children")

    # Bob must be taken
    model.addConstr(bob == 1, "bob_required")

    # If Alice is taken, Diana cannot be taken: alice + diana <= 1
    model.addConstr(alice + diana <= 1, "alice_diana")

    # If Bob is taken, Charlie cannot be taken: bob + charlie <= 1
    model.addConstr(bob + charlie <= 1, "bob_charlie")

    # If Charlie is taken, Diana must be taken: charlie <= diana
    model.addConstr(charlie <= diana, "charlie_diana")

    # If Diana is taken, Ella must be taken: diana <= ella
    model.addConstr(diana <= ella, "diana_ella")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}