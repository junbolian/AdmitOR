import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    fabrication_nodes = [0, 1, 2]
    testing_nodes = [3, 4, 5, 6]

    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    arc_cost = {arcs[i]: cost[i] for i in range(len(arcs))}
    arc_cap = {arcs[i]: capacity[i] for i in range(len(arcs))}

    # Node net supply: fabrication nodes have positive supply, testing nodes have negative
    node_supply = {}
    for idx, node in enumerate(fabrication_nodes):
        node_supply[node] = supply[idx]
    for idx, node in enumerate(testing_nodes):
        node_supply[node] = -demand[idx]

    model = gp.Model("wafer_transport")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= arc_cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow balance constraints
    all_nodes = fabrication_nodes + testing_nodes
    for node in all_nodes:
        outflow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        inflow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        model.addConstr(outflow - inflow == node_supply[node], name=f"balance_{node}")

    model.setObjective(
        gp.quicksum(arc_cost[arc] * flow[arc] for arc in arcs),
        GRB.MINIMIZE
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