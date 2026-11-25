import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params[f"arc_cost_{i}_{j}"]

    supply = {0: params["supply_node_0"], 7: -params["demand_node_7"]}
    for nd in range(1, 7):
        supply[nd] = 0

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in arcs), GRB.MINIMIZE)

    for nd in nodes:
        outflow = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == nd)
        inflow  = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == nd)
        model.addConstr(outflow - inflow == supply[nd], name=f"balance_{nd}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}