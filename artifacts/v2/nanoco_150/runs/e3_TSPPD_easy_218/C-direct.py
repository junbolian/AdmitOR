import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dist = params["distance_matrix"]
    n = 7  # fixed number of nodes (structural constant)
    num_req = 3  # fixed number of requisitions (structural constant)

    # Pickup-delivery pairs (structural, fixed by problem definition)
    # Requisition 0: pickup=4, delivery=6
    # Requisition 1: pickup=5, delivery=1
    # Requisition 2: pickup=2, delivery=3
    pickups    = [4, 5, 2]
    deliveries = [6, 1, 3]

    nodes = list(range(n))
    # All directed arcs excluding self-loops
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.Params.OutputFlag = 0

    # x[i,j] = 1 if arc (i,j) is used
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # u[i] = position of node i in tour (MTZ subtour elimination), depot fixed at 0
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each node has exactly one outgoing arc
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1, name=f"out_{i}")

    # Each node has exactly one incoming arc
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"in_{j}")

    # MTZ subtour elimination
    model.addConstr(u[0] == 0, name="depot_pos")
    for i in nodes[1:]:
        model.addConstr(u[i] >= 1, name=f"lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"ub_{i}")
    for (i, j) in arcs:
        if i != 0 and j != 0:
            model.addConstr(u[i] - u[j] + (n - 1) * x[i, j] <= n - 2, name=f"mtz_{i}_{j}")
        elif i == 0 and j != 0:
            # Depot departs first (u[0]=0), enforce for arcs leaving depot
            model.addConstr(u[j] >= 1 - (n - 1) * (1 - x[i, j]), name=f"mtz_dep_{j}")

    # Precedence constraints: pickup must be visited before delivery
    for k in range(num_req):
        p = pickups[k]
        d = deliveries[k]
        # u[p] < u[d]  =>  u[d] - u[p] >= 1
        model.addConstr(u[d] - u[p] >= 1, name=f"prec_{k}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}