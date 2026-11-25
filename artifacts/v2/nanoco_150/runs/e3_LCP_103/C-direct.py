import gurobipy as gp
from gurobipy import GRB

def solve(params):
    conflict_pairs = params["conflict_pairs"]
    allowable = {
        0: params["allowable_slots_exam0"],
        1: params["allowable_slots_exam1"],
        2: params["allowable_slots_exam2"],
        3: params["allowable_slots_exam3"],
        4: params["allowable_slots_exam4"],
        5: params["allowable_slots_exam5"],
        6: params["allowable_slots_exam6"],
        7: params["allowable_slots_exam7"],
    }

    num_exams = 8
    all_slots = set()
    for slots in allowable.values():
        all_slots.update(slots)
    all_slots = sorted(all_slots)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[e, s] = 1 if exam e is assigned to slot s
    x = {}
    for e in range(num_exams):
        for s in allowable[e]:
            x[e, s] = model.addVar(vtype=GRB.BINARY, name=f"x_{e}_{s}")

    # z = latest slot used (objective to minimize)
    z = model.addVar(vtype=GRB.INTEGER, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Each exam assigned exactly one slot from its allowable list
    for e in range(num_exams):
        model.addConstr(
            gp.quicksum(x[e, s] for s in allowable[e]) == 1,
            name=f"assign_{e}"
        )

    # Conflict constraints: conflicting exams must not share a slot
    for (e1, e2) in conflict_pairs:
        shared = set(allowable[e1]) & set(allowable[e2])
        for s in shared:
            model.addConstr(
                x[e1, s] + x[e2, s] <= 1,
                name=f"conflict_{e1}_{e2}_{s}"
            )

    # z >= s * x[e, s] for all e, s  =>  z is at least the assigned slot of every exam
    for e in range(num_exams):
        for s in allowable[e]:
            model.addConstr(
                z >= s * x[e, s],
                name=f"zlb_{e}_{s}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}