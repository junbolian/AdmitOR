import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    capacity = params["capacity"]
    cost = params["cost"]
    # coords not needed for the optimization model itself

    arcs = [(0,2),(0,3),(1,2),(1,3),(2,4),(2,5),(3,4),(3,5),(0,4),(0,5),(1,4),(1,5)]
    nodes = list(range(6))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    for i, arc in enumerate(arcs):
        model.addConstr(flow[arc] <= capacity[i], name=f"cap_{arc[0]}_{arc[1]}")

    for node in nodes:
        outflow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        inflow  = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        model.addConstr(outflow - inflow == supply[node], name=f"balance_{node}")

    model.setObjective(
        gp.quicksum(cost[i] * flow[arcs[i]] for i in range(len(arcs))),
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
        return {"objective": None, "status": f"gurobi_status_{status}"}