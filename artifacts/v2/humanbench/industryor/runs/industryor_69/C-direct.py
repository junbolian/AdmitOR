import math
from gurobipy import Model, GRB, quicksum


def solve(params):
    Q = float(params["vehicle_capacity"])
    demand = params["customer_demand"]
    e = params["earliest_service_time"]
    l = params["latest_service_time"]
    s = params["service_time"]
    xs = params["x_coordinate"]
    ys = params["y_coordinate"]

    N = list(range(len(demand)))   # 0 = depot, 1..n customers
    C = N[1:]                      # customers only

    def dist(i, j):
        return math.hypot(xs[i] - xs[j], ys[i] - ys[j])

    t = {(i, j): dist(i, j) for i in N for j in N if i != j}

    # Upper bound on fleet size: number of customers (each on own route)
    K = len(C)

    model = Model("VRPHTW")
    model.Params.OutputFlag = 0
    model.Params.TimeLimit = 600

    # x[i,j] = 1 if some vehicle travels directly from i to j
    x = model.addVars(
        [(i, j) for i in N for j in N if i != j],
        vtype=GRB.BINARY, name="x"
    )

    # w[i] = service start time at node i
    w = model.addVars(
        N,
        lb=[float(e[i]) for i in N],
        ub=[float(l[i]) for i in N],
        vtype=GRB.CONTINUOUS, name="w"
    )

    # u[i] = cumulative load delivered up to and including node i
    # For customers: demand[i] <= u[i] <= Q
    # Depot not needed in MTZ load formulation
    u = model.addVars(
        C,
        lb=[float(demand[i]) for i in C],
        ub=[Q for _ in C],
        vtype=GRB.CONTINUOUS, name="u"
    )

    # Objective: minimize total travel distance
    model.setObjective(
        quicksum(t[i, j] * x[i, j] for i in N for j in N if i != j),
        GRB.MINIMIZE
    )

    # Each customer has exactly one incoming and one outgoing arc
    for i in C:
        model.addConstr(quicksum(x[i, j] for j in N if j != i) == 1,
                        name=f"out_{i}")
        model.addConstr(quicksum(x[j, i] for j in N if j != i) == 1,
                        name=f"in_{i}")

    # Number of vehicles leaving depot == number returning (at most K)
    model.addConstr(quicksum(x[0, j] for j in C) <= K, name="max_routes")
    model.addConstr(
        quicksum(x[0, j] for j in C) == quicksum(x[i, 0] for i in C),
        name="depot_balance"
    )

    # Hard time window propagation for all arcs (i -> j), j in C
    # If x[i,j]=1 then w[j] >= w[i] + s[i] + t[i,j]
    for i in N:
        for j in C:
            if i == j:
                continue
            # Big-M: largest possible gap
            M_ij = max(0.0, float(l[i]) + float(s[i]) + t[i, j] - float(e[j]))
            if M_ij > 0:
                model.addConstr(
                    w[j] >= w[i] + float(s[i]) + t[i, j] - M_ij * (1 - x[i, j]),
                    name=f"tw_{i}_{j}"
                )

    # Also enforce time window for arcs returning to depot
    for i in C:
        M_i0 = max(0.0, float(l[i]) + float(s[i]) + t[i, 0] - float(e[0]))
        if M_i0 > 0:
            model.addConstr(
                w[0] >= w[i] + float(s[i]) + t[i, 0] - M_i0 * (1 - x[i, 0]),
                name=f"tw_{i}_depot"
            )

    # Capacity propagation (MTZ-style): if x[i,j]=1 and both are customers
    # then u[j] >= u[i] + demand[j]
    for i in C:
        for j in C:
            if i != j:
                model.addConstr(
                    u[j] >= u[i] + float(demand[j]) - Q * (1 - x[i, j]),
                    name=f"cap_{i}_{j}"
                )

    # If depot -> customer j, load at j is exactly demand[j]
    # (u[j] >= demand[j] is already the lower bound, but we need an upper bound
    #  when coming from depot to prevent false capacity slack)
    for j in C:
        model.addConstr(
            u[j] <= Q - (Q - float(demand[j])) * x[0, j],
            name=f"cap_depot_{j}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjBound), "status": "time_limit"}
        else:
            return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"status_{status}"}