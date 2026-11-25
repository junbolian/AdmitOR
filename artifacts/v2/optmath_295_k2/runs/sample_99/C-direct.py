import gurobipy as gp
from gurobipy import GRB

def solve(params):
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    # Directed arcs in order: (0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)
    arcs = [(0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)]
    nodes = [0, 1, 2, 3]

    arc_index = {arc: i for i, arc in enumerate(arcs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish connection
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # Continuous: flow on each arc
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[arc_index[a]] * y[a] + variable_cost[arc_index[a]] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: x[a] <= capacity[a] * y[a]
    for a in arcs:
        idx = arc_index[a]
        model.addConstr(x[a] <= capacity[idx] * y[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: sum of incoming - sum of outgoing = net_demand[node]
    for node in nodes:
        incoming = gp.quicksum(x[a] for a in arcs if a[1] == node)
        outgoing = gp.quicksum(x[a] for a in arcs if a[0] == node)
        model.addConstr(incoming - outgoing == net_demand[node], name=f"balance_{node}")

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