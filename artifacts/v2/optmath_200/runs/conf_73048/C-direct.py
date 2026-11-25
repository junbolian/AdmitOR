import gurobipy as gp
from gurobipy import GRB

def solve(params):
    net_supply = params["net_supply"]
    transport_cost = params["transport_cost"]
    node_capacity = params["node_capacity"]
    link_capacity = params["link_capacity"]

    n = 7
    cities = range(n)

    # Build list of directed links (i->j) excluding self-loops, row-major by source
    links = [(i, j) for i in cities for j in cities if i != j]

    # Map link index to (i,j)
    cost = {links[k]: transport_cost[k] for k in range(len(links))}
    cap = {links[k]: link_capacity[k] for k in range(len(links))}

    model = gp.Model("resource_distribution")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(links, lb=0.0, name="flow")

    # Link capacity constraints
    for (i, j) in links:
        model.addConstr(flow[i, j] <= cap[i, j], name=f"link_cap_{i}_{j}")

    # Node capacity constraints (on total incoming flow)
    for j in cities:
        model.addConstr(
            gp.quicksum(flow[i, j] for i in cities if i != j) <= node_capacity[j],
            name=f"node_cap_{j}"
        )

    # Flow balance constraints: outflow - inflow = net_supply
    for i in cities:
        outflow = gp.quicksum(flow[i, j] for j in cities if j != i)
        inflow = gp.quicksum(flow[j, i] for j in cities if j != i)
        model.addConstr(outflow - inflow == net_supply[i], name=f"balance_{i}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(cost[i, j] * flow[i, j] for (i, j) in links),
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
        return {"objective": None, "status": f"status_{model.Status}"}