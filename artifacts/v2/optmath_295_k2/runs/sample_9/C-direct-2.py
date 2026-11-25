import gurobipy as gp
from gurobipy import GRB

def solve(params):
    node_net_outflow = params["node_net_outflow"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    # Arc ordering as specified
    arcs = [
        (0,1),(1,0),(0,2),(2,0),(0,3),(3,0),(0,4),(4,0),(0,5),(5,0),(0,6),(6,0),
        (1,2),(2,1),(1,3),(3,1),(1,4),(4,1),(1,5),(5,1),(1,6),(6,1),
        (2,3),(3,2),(2,4),(4,2),(2,5),(5,2),(2,6),(6,2),
        (3,4),(4,3),(3,5),(5,3),(3,6),(6,3),
        (4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5)
    ]

    arc_index = {arc: i for i, arc in enumerate(arcs)}
    nodes = list(range(7))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish arc
    y = model.addVars(len(arcs), vtype=GRB.BINARY, name="y")
    # Continuous: flow on arc
    x = model.addVars(len(arcs), lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] + variable_cost[i] * x[i] for i in range(len(arcs))),
        GRB.MINIMIZE
    )

    # Capacity constraints: x[i] <= capacity[i] * y[i]
    for i in range(len(arcs)):
        model.addConstr(x[i] <= capacity[i] * y[i], name=f"cap_{i}")

    # Flow balance: for each node, outflow - inflow = net_outflow
    for node in nodes:
        outgoing = [arc_index[(node, j)] for j in nodes if (node, j) in arc_index]
        incoming = [arc_index[(j, node)] for j in nodes if (j, node) in arc_index]
        model.addConstr(
            gp.quicksum(x[k] for k in outgoing) - gp.quicksum(x[k] for k in incoming)
            == node_net_outflow[node],
            name=f"balance_{node}"
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
        return {"objective": None, "status": f"solver_status_{status}"}