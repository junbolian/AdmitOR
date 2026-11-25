import gurobipy as gp
from gurobipy import GRB

def solve(params):
    node_net_outflow = params["node_net_outflow"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    # Directed arcs in order
    arcs = [
        (0,1),(1,0),(0,2),(2,0),(0,3),(3,0),(0,4),(4,0),(0,5),(5,0),(0,6),(6,0),
        (1,2),(2,1),(1,3),(3,1),(1,4),(4,1),(1,5),(5,1),(1,6),(6,1),
        (2,3),(3,2),(2,4),(4,2),(2,5),(5,2),(2,6),(6,2),
        (3,4),(4,3),(3,5),(5,3),(3,6),(6,3),
        (4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5)
    ]

    num_nodes = 7
    arc_indices = range(len(arcs))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish arc
    y = model.addVars(arc_indices, vtype=GRB.BINARY, name="y")
    # Continuous: flow on arc
    x = model.addVars(arc_indices, lb=0.0, name="x")

    # Objective: fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[k] * y[k] + variable_cost[k] * x[k] for k in arc_indices),
        GRB.MINIMIZE
    )

    # Flow balance: outflow - inflow = net_outflow
    for node in range(num_nodes):
        out_arcs = [k for k, (i, j) in enumerate(arcs) if i == node]
        in_arcs  = [k for k, (i, j) in enumerate(arcs) if j == node]
        model.addConstr(
            gp.quicksum(x[k] for k in out_arcs) - gp.quicksum(x[k] for k in in_arcs)
            == node_net_outflow[node],
            name=f"balance_{node}"
        )

    # Capacity and linking constraints
    for k in arc_indices:
        model.addConstr(x[k] <= capacity[k] * y[k], name=f"cap_{k}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}