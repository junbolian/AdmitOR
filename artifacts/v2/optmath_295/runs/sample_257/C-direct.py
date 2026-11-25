import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_node0 = params["supply_node0"]
    demand_node7 = params["demand_node7"]
    route_costs_flat = params["route_costs"]

    n_nodes = 8
    # Build cost dict: cost[(i,j)] for i != j
    # Order: for each i in 0..7, for each j in 0..7 excluding i, in order 0,1,...,7 skipping i
    cost = {}
    idx = 0
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j:
                cost[(i, j)] = route_costs_flat[idx]
                idx += 1

    arcs = list(cost.keys())

    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)

    # Flow balance constraints
    for node in range(n_nodes):
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == node)
        inflow  = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == node)
        if node == 0:
            # net outflow = supply_node0
            model.addConstr(outflow - inflow == supply_node0, name=f"balance_{node}")
        elif node == 7:
            # net inflow = demand_node7
            model.addConstr(inflow - outflow == demand_node7, name=f"balance_{node}")
        else:
            # flow conservation
            model.addConstr(inflow - outflow == 0, name=f"balance_{node}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}