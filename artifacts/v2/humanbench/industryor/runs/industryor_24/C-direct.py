import gurobipy as gp
from gurobipy import GRB

def solve(params):
    requirements = params["requirements"]  # list of 6 values
    shift_length = params["shift_length"]  # 8 hours
    period_length = params["period_length"]  # 4 hours

    # Number of consecutive periods each crew member covers
    periods_covered = int(shift_length / period_length)  # = 2

    # 6 shifts, indexed 0..5
    num_shifts = 6

    # x[i] = number of crew members starting at shift i (0-indexed)
    # A crew member starting at shift i covers shifts i and i+1 (mod 6)

    model = gp.Model("bus_crew")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_shifts, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total crew
    model.setObjective(gp.quicksum(x[i] for i in range(num_shifts)), GRB.MINIMIZE)

    # Coverage constraints: for each shift s, sum of x[i] where i covers s >= requirements[s]
    # Crew starting at shift i covers shift i and shift (i+1) mod num_shifts
    for s in range(num_shifts):
        # Shifts that cover period s: shift s itself, and shift (s-1) mod num_shifts
        covering = [(s - k) % num_shifts for k in range(periods_covered)]
        model.addConstr(
            gp.quicksum(x[i] for i in covering) >= requirements[s],
            name=f"cover_{s}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}