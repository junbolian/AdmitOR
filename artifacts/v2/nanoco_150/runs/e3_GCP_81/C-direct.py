import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_courses = params["num_courses"]
    num_edges = params["num_edges"]
    min_slots = params["min_slots"]
    max_slots = params["max_slots"]
    edge_list = params["edge_list"]
    slot_cost = params["slot_cost"]

    model = gp.Model("exam_scheduling")
    model.Params.OutputFlag = 0
    model.Params.TimeLimit = 120

    courses = range(num_courses)
    slots = range(max_slots)

    x = model.addVars(num_courses, max_slots, vtype=GRB.BINARY, name="x")
    y = model.addVars(max_slots, vtype=GRB.BINARY, name="y")

    for v in courses:
        model.addConstr(gp.quicksum(x[v, k] for k in slots) == 1, name=f"assign_{v}")

    for e_idx, (u, w) in enumerate(edge_list):
        for k in slots:
            model.addConstr(x[u, k] + x[w, k] <= 1, name=f"conflict_{e_idx}_{k}")

    for v in courses:
        for k in slots:
            model.addConstr(x[v, k] <= y[k], name=f"link_{v}_{k}")

    for k in range(1, max_slots):
        model.addConstr(y[k] <= y[k - 1], name=f"order_{k}")

    model.addConstr(gp.quicksum(y[k] for k in slots) >= min_slots, name="min_slots_lb")

    model.setObjective(slot_cost * gp.quicksum(y[k] for k in slots), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        reason = "infeasible" if model.status == GRB.INFEASIBLE else f"status_{model.status}"
        return {"objective": None, "status": reason}