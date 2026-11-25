import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supplies = params["node_supplies"]
    # node_coordinates not needed for optimization, only topology matters

    arcs = [
        (0,1),(0,7),(1,2),(1,7),(2,3),(2,6),(3,4),(3,5),(3,8),(3,9),
        (4,5),(4,8),(5,6),(6,7),(7,8),(7,9),(8,9)
    ]
    num_nodes = 10

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables for each arc
    flow = {}
    for idx, (i, j) in enumerate(arcs):
        flow[(i,j)] = model.addVar(
            lb=0,
            ub=arc_capacities[idx],
            obj=arc_costs[idx],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{i}_{j}"
        )

    model.ModelSense = GRB.MINIMIZE

    # Flow conservation constraints
    for node in range(num_nodes):
        outflow = gp.quicksum(flow[(i,j)] for (i,j) in arcs if i == node)
        inflow  = gp.quicksum(flow[(i,j)] for (i,j) in arcs if j == node)
        model.addConstr(outflow - inflow == node_supplies[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}