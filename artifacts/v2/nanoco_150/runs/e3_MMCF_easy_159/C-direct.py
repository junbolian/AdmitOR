import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    node_x = params["node_x"]
    node_y = params["node_y"]
    demand = params["demand"]

    # Arc definitions (fixed topology)
    arcs = [
        (0,1),(1,0),(0,4),(4,0),(1,2),(2,1),(1,3),(3,1),(1,5),(5,1),(1,6),(6,1),
        (2,3),(3,2),(3,4),(4,3),(4,5),(5,4),(5,6),(6,5),(5,9),(9,5),(6,7),(7,6),
        (7,8),(8,7),(7,9),(9,7),(8,9),(9,8)
    ]
    num_arcs = len(arcs)
    nodes = list(range(10))

    # Requests: (source, sink, demand)
    requests = [
        (1, 4, demand[0]),
        (7, 9, demand[1]),
    ]
    num_requests = len(requests)

    # Build adjacency for outgoing/incoming arcs per node
    # arc_index[(i,j)] = index in arcs list
    arc_index = {(i, j): k for k, (i, j) in enumerate(arcs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: f[r][k] = flow for request r on arc k
    f = {}
    for r in range(num_requests):
        for k in range(num_arcs):
            f[r, k] = model.addVar(lb=0.0, name=f"f_{r}_{k}")

    # Auxiliary variable for minimax utilization
    u_max = model.addVar(lb=0.0, name="u_max")

    model.update()

    # Flow conservation constraints for each request
    for r, (src, snk, dem) in enumerate(requests):
        for node in nodes:
            outflow = gp.LinExpr()
            inflow = gp.LinExpr()
            for k, (i, j) in enumerate(arcs):
                if i == node:
                    outflow += f[r, k]
                if j == node:
                    inflow += f[r, k]
            if node == src:
                model.addConstr(outflow - inflow == dem, name=f"flow_src_r{r}_n{node}")
            elif node == snk:
                model.addConstr(inflow - outflow == dem, name=f"flow_snk_r{r}_n{node}")
            else:
                model.addConstr(outflow - inflow == 0, name=f"flow_bal_r{r}_n{node}")

    # Capacity constraints and utilization upper bound
    for k in range(num_arcs):
        cap = arc_capacity[k]
        total_flow = gp.quicksum(f[r, k] for r in range(num_requests))
        # Aggregate flow <= capacity
        model.addConstr(total_flow <= cap, name=f"cap_{k}")
        # u_max >= utilization of arc k
        if cap > 0:
            model.addConstr(u_max >= total_flow / cap, name=f"util_{k}")

    # Objective: minimize maximum utilization rate
    model.setObjective(u_max, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}