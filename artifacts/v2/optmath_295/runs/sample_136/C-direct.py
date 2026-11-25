import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    source_supply = params["source_supply"]
    sink_demand = params["sink_demand"]

    n = 7
    nodes = range(n)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i, j in arcs),
        GRB.MINIMIZE
    )

    for node in nodes:
        outflow = gp.quicksum(x[node, j] for j in nodes if j != node)
        inflow = gp.quicksum(x[i, node] for i in nodes if i != node)

        if node == 0:
            model.addConstr(outflow - inflow == source_supply, name=f"balance_{node}")
        elif node == 6:
            model.addConstr(inflow - outflow == sink_demand, name=f"balance_{node}")
        else:
            model.addConstr(inflow - outflow == 0, name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}