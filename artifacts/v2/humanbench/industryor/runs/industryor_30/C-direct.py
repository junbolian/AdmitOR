import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dur = {
        "A": float(params["duration_A"]),
        "B": float(params["duration_B"]),
        "C": float(params["duration_C"]),
        "D": float(params["duration_D"]),
        "E": float(params["duration_E"]),
        "F": float(params["duration_F"]),
        "G": float(params["duration_G"]),
    }
    work_cost = float(params["daily_work_cost"])
    mach_cost = float(params["daily_machinery_cost"])

    acts = list(dur.keys())

    model = gp.Model("project_scheduling")
    model.ModelSense = GRB.MINIMIZE

    start = {a: model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"start_{a}")
             for a in acts}
    # project completion time
    finish = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="finish")

    # machinery rental window: from start of A to end of B
    rental = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="rental_days")

    # precedence constraints: pred must finish before succ starts
    precedence = [
        ("A", "G"), ("A", "D"),
        ("E", "F"), ("G", "F"),
        ("D", "C"), ("F", "C"),
        ("F", "B"),
    ]
    for pred, succ in precedence:
        model.addConstr(start[succ] >= start[pred] + dur[pred],
                        name=f"prec_{pred}_{succ}")

    # finish time of the project
    for a in acts:
        model.addConstr(finish >= start[a] + dur[a], name=f"finish_{a}")

    # machinery rented from start of A to end of B
    model.addConstr(rental >= start["B"] + dur["B"] - start["A"],
                    name="rental_window")
    model.addConstr(rental >= 0)

    # objective: daily work cost over project duration + machinery rental cost
    model.setObjective(work_cost * finish + mach_cost * rental, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed: {model.Status}"}