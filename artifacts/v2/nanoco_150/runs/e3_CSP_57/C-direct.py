import gurobipy as gp
from gurobipy import GRB
from itertools import product as iproduct


def solve(params):
    master_width = params["master_width"]
    order_quantities = params["order_quantities"]  # list of 3 ints
    finished_widths = params["finished_widths"]    # list of 3 widths

    n_types = len(finished_widths)

    # Enumerate all feasible cutting patterns
    # A pattern is a tuple (a0, a1, a2) where ai is the number of rolls of type i cut
    # Constraint: sum(ai * wi) <= master_width, ai >= 0 integer
    patterns = []
    max_cuts = [int(master_width // finished_widths[i]) for i in range(n_types)]

    for combo in iproduct(*[range(m + 1) for m in max_cuts]):
        if sum(combo[i] * finished_widths[i] for i in range(n_types)) <= master_width:
            # Exclude the trivial all-zero pattern
            if any(c > 0 for c in combo):
                patterns.append(combo)

    if not patterns:
        return {"objective": None, "status": "no feasible patterns"}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = number of master rolls cut using pattern j (integer >= 0)
    x = model.addVars(len(patterns), vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total master rolls used
    model.setObjective(gp.quicksum(x[j] for j in range(len(patterns))), GRB.MINIMIZE)

    # Demand constraints: each finished roll type must meet its order quantity
    for i in range(n_types):
        model.addConstr(
            gp.quicksum(patterns[j][i] * x[j] for j in range(len(patterns))) >= order_quantities[i],
            name=f"demand_{i}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}