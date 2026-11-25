import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    net_demands = params["net_demands"]
    city_capacity = params["city_capacity"]
    link_capacity = params["link_capacity"]

    n_cities = 7
    # Directed links: for each source i, destinations are all j != i, ordered by j
    # Order: 0->1,0->2,...,0->6, 1->0,1->2,...,1->6, ...
    links = []
    for i in range(n_cities):
        for j in range(n_cities):
            if i != j:
                links.append((i, j))

    # Build cost and capacity dicts indexed by (i,j)
    cost = {links[k]: costs[k] for k in range(len(links))}
    cap_link = {links[k]: link_capacity[k] for k in range(len(links))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(links, lb=0.0, name="flow")

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[i, j] * flow[i, j] for (i, j) in links),
        GRB.MINIMIZE
    )

    # Flow balance: inflow - outflow = net_demand[i]
    for i in range(n_cities):
        inflow = gp.quicksum(flow[j, i] for j in range(n_cities) if j != i)
        outflow = gp.quicksum(flow[i, j] for j in range(n_cities) if j != i)
        model.addConstr(inflow - outflow == net_demands[i], name=f"balance_{i}")

    # Link capacity constraints
    for (i, j) in links:
        model.addConstr(flow[i, j] <= cap_link[i, j], name=f"linkcap_{i}_{j}")

    # City receiving capacity constraints
    for i in range(n_cities):
        inflow = gp.quicksum(flow[j, i] for j in range(n_cities) if j != i)
        model.addConstr(inflow <= city_capacity[i], name=f"citycap_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}