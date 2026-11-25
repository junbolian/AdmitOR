import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    net_demands = params["net_demands"]
    city_capacity = params["city_capacity"]
    link_capacity = params["link_capacity"]

    n_cities = 7
    # All directed links: (i, j) for i != j, ordered as (0->1,0->2,...,0->6,1->0,...)
    links = [(i, j) for i in range(n_cities) for j in range(n_cities) if i != j]

    cost = {links[k]: costs[k] for k in range(len(links))}
    cap_link = {links[k]: link_capacity[k] for k in range(len(links))}
    cap_city = {i: city_capacity[i] for i in range(n_cities)}
    demand = {i: net_demands[i] for i in range(n_cities)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed link
    flow = model.addVars(links, lb=0.0, name="flow")

    # Link capacity constraints
    for lnk in links:
        model.addConstr(flow[lnk] <= cap_link[lnk], name=f"linkcap_{lnk[0]}_{lnk[1]}")

    # City receiving capacity constraints
    for i in range(n_cities):
        inflow = gp.quicksum(flow[j, i] for j in range(n_cities) if j != i)
        model.addConstr(inflow <= cap_city[i], name=f"citycap_{i}")

    # Flow balance: inflow - outflow = net_demand
    # positive net_demand means city receives more than it sends (net consumer)
    # negative net_demand means city sends more than it receives (net supplier)
    for i in range(n_cities):
        inflow = gp.quicksum(flow[j, i] for j in range(n_cities) if j != i)
        outflow = gp.quicksum(flow[i, j] for j in range(n_cities) if j != i)
        model.addConstr(inflow - outflow == demand[i], name=f"balance_{i}")

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[lnk] * flow[lnk] for lnk in links),
        GRB.MINIMIZE
    )

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