import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    regular_wage = params["regular_wage"]
    contract_wage = params["contract_wage"]
    shift_hours = params["shift_hours"]
    num_periods = params["num_periods"]
    num_shift_starts = params["num_shift_starts"]

    # Each shift covers 2 consecutive 4-hour periods (8 hours / 4 hours per period = 2 periods)
    periods_per_shift = shift_hours // 4

    # Shift i (0-indexed) starting at period i covers periods i and (i+1) mod num_periods
    # regular[i] = regular nurses starting at shift i
    # contract[i] = contract nurses starting at shift i

    model = gp.Model("nurse_scheduling")
    model.setParam("OutputFlag", 0)

    regular = model.addVars(num_shift_starts, vtype=GRB.INTEGER, lb=0, name="regular")
    contract = model.addVars(num_shift_starts, vtype=GRB.INTEGER, lb=0, name="contract")

    # Objective: minimize total cost
    # Each nurse works shift_hours hours per shift
    obj = gp.quicksum(
        (regular[i] * regular_wage + contract[i] * contract_wage) * shift_hours
        for i in range(num_shift_starts)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Coverage constraints: for each period p, sum of nurses whose shift covers period p >= demand[p]
    for p in range(num_periods):
        covering_shifts = [
            i for i in range(num_shift_starts)
            if p in [(i + k) % num_periods for k in range(int(periods_per_shift))]
        ]
        model.addConstr(
            gp.quicksum(regular[i] + contract[i] for i in covering_shifts) >= demand[p],
            name=f"demand_period_{p}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}