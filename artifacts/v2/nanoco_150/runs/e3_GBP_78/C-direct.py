import gurobipy as gp
from gurobipy import GRB

def solve(params):
    frame_width = params["frame_width"]
    frame_height = params["frame_height"]
    array_widths = params["array_widths"]
    array_heights = params["array_heights"]

    n_arrays = 4
    # Upper bound on frames needed: each array in its own frame
    max_frames = n_arrays

    arrays = range(n_arrays)
    frames = range(max_frames)

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,k]: x-coordinate (left edge) of array i in frame k
    x = model.addVars(n_arrays, max_frames, lb=0.0, name="x")
    # y[i,k]: y-coordinate (bottom edge) of array i in frame k
    y = model.addVars(n_arrays, max_frames, lb=0.0, name="y")
    # assign[i,k]: 1 if array i is assigned to frame k
    assign = model.addVars(n_arrays, max_frames, vtype=GRB.BINARY, name="assign")
    # use[k]: 1 if frame k is used
    use = model.addVars(max_frames, vtype=GRB.BINARY, name="use")

    # Objective: minimize number of frames used
    model.setObjective(gp.quicksum(use[k] for k in frames), GRB.MINIMIZE)

    # Each array assigned to exactly one frame
    for i in arrays:
        model.addConstr(gp.quicksum(assign[i, k] for k in frames) == 1)

    # Frame used if any array assigned to it
    for k in frames:
        for i in arrays:
            model.addConstr(use[k] >= assign[i, k])

    # Symmetry breaking: frame k can only be used if frame k-1 is used
    for k in range(1, max_frames):
        model.addConstr(use[k] <= use[k - 1])

    # Big-M for containment constraints
    M_x = frame_width
    M_y = frame_height

    # Array must fit within frame boundaries when assigned
    for i in arrays:
        wi = array_widths[i]
        hi = array_heights[i]
        for k in frames:
            # x[i,k] + wi <= frame_width when assigned
            model.addConstr(x[i, k] + wi <= frame_width + M_x * (1 - assign[i, k]))
            # y[i,k] + hi <= frame_height when assigned
            model.addConstr(y[i, k] + hi <= frame_height + M_y * (1 - assign[i, k]))
            # x[i,k] >= 0 is already enforced by lb; but when not assigned, x can be anything >= 0
            # Upper bound on x and y when not assigned (keep variables bounded)
            model.addConstr(x[i, k] <= M_x * assign[i, k])
            model.addConstr(y[i, k] <= M_y * assign[i, k])

    # Non-overlap constraints for pairs of arrays on the same frame
    # For each pair (i, j) with i < j on frame k, at least one separation must hold:
    #   i is left of j, i is right of j, i is below j, i is above j
    # Introduce binary variables to select which separation applies
    # sep[i,j,k,d]: separation direction d in {0,1,2,3}
    pairs = [(i, j) for i in arrays for j in arrays if i < j]

    sep = model.addVars(
        [(i, j, k, d) for (i, j) in pairs for k in frames for d in range(4)],
        vtype=GRB.BINARY,
        name="sep"
    )

    for (i, j) in pairs:
        wi = array_widths[i]
        hi = array_heights[i]
        wj = array_widths[j]
        hj = array_heights[j]
        for k in frames:
            # Both assigned to k => at least one separation
            # sum of sep directions >= 1 when both assigned to k
            both = model.addVar(vtype=GRB.BINARY, name=f"both_{i}_{j}_{k}")
            model.addConstr(both <= assign[i, k])
            model.addConstr(both <= assign[j, k])
            model.addConstr(both >= assign[i, k] + assign[j, k] - 1)

            model.addConstr(gp.quicksum(sep[i, j, k, d] for d in range(4)) >= both)

            big = frame_width + frame_height

            # d=0: i left of j => x[i,k] + wi <= x[j,k]
            model.addConstr(x[i, k] + wi <= x[j, k] + big * (1 - sep[i, j, k, 0]))
            # d=1: j left of i => x[j,k] + wj <= x[i,k]
            model.addConstr(x[j, k] + wj <= x[i, k] + big * (1 - sep[i, j, k, 1]))
            # d=2: i below j => y[i,k] + hi <= y[j,k]
            model.addConstr(y[i, k] + hi <= y[j, k] + big * (1 - sep[i, j, k, 2]))
            # d=3: j below i => y[j,k] + hj <= y[i,k]
            model.addConstr(y[j, k] + hj <= y[i, k] + big * (1 - sep[i, j, k, 3]))

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjVal), "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}