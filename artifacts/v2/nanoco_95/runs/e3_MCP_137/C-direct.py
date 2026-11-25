import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    interference_edges = params["interference_edges"]

    n_devices = 8
    devices = range(n_devices)

    # Upper bound on makespan: sum of all durations
    T_ub = sum(durations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start time for each device
    start = model.addVars(devices, lb=0, ub=T_ub, vtype=GRB.CONTINUOUS, name="start")

    # Makespan variable
    makespan = model.addVar(lb=0, ub=T_ub, vtype=GRB.CONTINUOUS, name="makespan")

    # Makespan >= start[i] + duration[i] for all i
    for i in devices:
        model.addConstr(makespan >= start[i] + durations[i], name=f"mkspan_{i}")

    # For each interference edge (i, j), the intervals must not overlap.
    # Either i finishes before j starts, or j finishes before i starts.
    # Introduce binary variable b[i,j]: 1 => i before j, 0 => j before i
    b = {}
    for edge in interference_edges:
        i, j = edge
        b[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"b_{i}_{j}")

        # If b=1: start[i] + durations[i] <= start[j]
        model.addConstr(
            start[i] + durations[i] <= start[j] + T_ub * (1 - b[(i, j)]),
            name=f"no_overlap_ij_{i}_{j}"
        )
        # If b=0: start[j] + durations[j] <= start[i]
        model.addConstr(
            start[j] + durations[j] <= start[i] + T_ub * b[(i, j)],
            name=f"no_overlap_ji_{i}_{j}"
        )

    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(makespan.X), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}