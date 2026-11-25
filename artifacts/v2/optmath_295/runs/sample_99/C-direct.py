import gurobipy as gp
from gurobipy import GRB

def solve(params):
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]
    num_nodes = params["num_nodes"]

    # Directed edges in order: (0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)
    edges = [
        (0,1),(0,2),(0,3),
        (1,0),(1,2),(1,3),
        (2,0),(2,1),(2,3),
        (3,0),(3,1),(3,2)
    ]
    edge_index = {e: i for i, e in enumerate(edges)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish connection on edge e
    y = model.addVars(len(edges), vtype=GRB.BINARY, name="y")
    # Continuous: flow on edge e
    x = model.addVars(len(edges), vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] + variable_cost[i] * x[i] for i in range(len(edges))),
        GRB.MINIMIZE
    )

    # Capacity and linking constraints
    for i, (u, v) in enumerate(edges):
        model.addConstr(x[i] <= capacity[i] * y[i], name=f"cap_{u}_{v}")

    # Flow balance: inflow - outflow = net_demand[n]
    nodes = range(num_nodes)
    for n in nodes:
        inflow = gp.quicksum(x[edge_index[(u, n)]] for (u, v) in edges if v == n)
        outflow = gp.quicksum(x[edge_index[(n, v)]] for (u, v) in edges if u == n)
        model.addConstr(inflow - outflow == net_demand[n], name=f"balance_{n}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}