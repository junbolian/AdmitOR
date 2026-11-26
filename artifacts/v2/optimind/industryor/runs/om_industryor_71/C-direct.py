import gurobipy as gp
from gurobipy import GRB


def solve(params):
    names = ["alice", "bob", "charlie", "diana", "ella"]
    costs = {n: float(params[f"cost_{n}"]) for n in names}
    max_children = int(params["max_children"])
    min_children = int(params["min_children"])

    model = gp.Model("li_family_trip")
    model.Params.OutputFlag = 0

    take = {n: model.addVar(vtype=GRB.BINARY, name=f"take_{n}") for n in names}

    # Bob is definitely taken
    model.addConstr(take["bob"] == 1)

    # Number of children between min and max
    model.addConstr(gp.quicksum(take[n] for n in names) <= max_children)
    model.addConstr(gp.quicksum(take[n] for n in names) >= min_children)

    # Alice and Diana are incompatible
    model.addConstr(take["alice"] + take["diana"] <= 1)

    # Bob and Charlie are incompatible
    model.addConstr(take["bob"] + take["charlie"] <= 1)

    # Charlie implies Diana
    model.addConstr(take["charlie"] <= take["diana"])

    # Diana implies Ella
    model.addConstr(take["diana"] <= take["ella"])

    model.setObjective(gp.quicksum(costs[n] * take[n] for n in names), GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        chosen = [n for n in names if take[n].X > 0.5]
        return {"objective": float(model.ObjVal), "status": "optimal", "chosen": chosen}

    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.Status}"}