import gurobipy as gp
from gurobipy import GRB

def solve(params):
    transport_cost = params["transport_cost"]
    node_net_demand = params["node_net_demand"]
    node_capacity = params["node_capacity"]
    link_capacity = params["link_capacity"]

    n = 7
    # Build list of directed links: (i, j) for i != j, ordered as (0->1,...,0->6, 1->0,...,6->5)
    links = [(i, j) for i in range(n) for j in range(n) if i != j]

    cost = {links[k]: transport_cost[k] for k in range(len(links))}
    cap_link = {links[k]: link_capacity[k] for k in range(len(links))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(links, lb=0.0, name="flow")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(cost[i, j] * flow[i, j] for (i, j) in links),
        GRB.MINIMIZE
    )

    # Flow balance: inflow - outflow = net_demand for each node
    for i in range(n):
        inflow = gp.quicksum(flow[j, i] for (j, k) in links if k == i)
        outflow = gp.quicksum(flow[i, j] for (k, j) in links if k == i)
        model.addConstr(inflow - outflow == node_net_demand[i], name=f"balance_{i}")

    # Node receiving capacity: total inflow <= node_capacity
    for i in range(n):
        inflow = gp.quicksum(flow[j, i] for (j, k) in links if k == i)
        model.addConstr(inflow <= node_capacity[i], name=f"node_cap_{i}")

    # Link capacity constraints
    for (i, j) in links:
        model.addConstr(flow[i, j] <= cap_link[i, j], name=f"link_cap_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}