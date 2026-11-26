import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]

    # 8 cities: 0 = source, 7 = destination
    n = 8
    source = 0
    sink = 7

    # Support both flat list and list-of-lists for capacity matrix
    def get_cap(i, j):
        if isinstance(capacity[0], (list, tuple)):
            return capacity[i][j]
        else:
            return capacity[i * n + j]

    # Build capacity dict
    cap = {}
    for i in range(n):
        for j in range(n):
            cap[(i, j)] = get_cap(i, j)

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge
    flow = {}
    for i in range(n):
        for j in range(n):
            flow[(i, j)] = model.addVar(lb=0.0, ub=cap[(i, j)], name=f"f_{i}_{j}")

    # Net outflow from source
    net_out_source = (
        gp.quicksum(flow[(source, j)] for j in range(n)) -
        gp.quicksum(flow[(i, source)] for i in range(n))
    )

    # Objective: maximize net flow out of source
    model.setObjective(net_out_source, GRB.MAXIMIZE)

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, node)] for i in range(n))
        outflow = gp.quicksum(flow[(node, j)] for j in range(n))
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    # Balance: net outflow from source equals net inflow to sink
    net_in_sink = (
        gp.quicksum(flow[(i, sink)] for i in range(n)) -
        gp.quicksum(flow[(sink, j)] for j in range(n))
    )
    model.addConstr(net_out_source == net_in_sink, name="source_sink_balance")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}