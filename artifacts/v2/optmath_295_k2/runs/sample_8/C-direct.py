import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_list = params["cost"]
    net_outflow_0 = params["net_outflow_node_0"]
    net_inflow_7 = params["net_inflow_node_7"]

    n = 8
    nodes = list(range(n))

    # Build arc list in the order specified: for each i in 0..7, for each j in 0..7, j != i
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    arc_cost = {arcs[k]: cost_list[k] for k in range(len(arcs))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(arc_cost[a] * x[a] for a in arcs), GRB.MINIMIZE)

    for node in nodes:
        outflow = gp.quicksum(x[(node, j)] for j in nodes if j != node)
        inflow = gp.quicksum(x[(i, node)] for i in nodes if i != node)
        if node == 0:
            model.addConstr(outflow - inflow == net_outflow_0, name=f"flow_{node}")
        elif node == 7:
            model.addConstr(inflow - outflow == net_inflow_7, name=f"flow_{node}")
        else:
            model.addConstr(inflow - outflow == 0, name=f"flow_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}