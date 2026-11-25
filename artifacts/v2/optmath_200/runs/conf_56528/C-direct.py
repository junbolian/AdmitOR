import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_node0 = params["supply_node0"]
    demand_node6 = params["demand_node6"]
    cost_matrix = params["cost_matrix"]

    n = 7
    nodes = range(n)

    # Build list of valid arcs (excluding self-loops)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for i in nodes:
        outflow = gp.quicksum(x[i, j] for j in nodes if i != j)
        inflow  = gp.quicksum(x[j, i] for j in nodes if j != i)
        if i == 0:
            # Supply node: net outflow = supply_node0
            model.addConstr(outflow - inflow == supply_node0, name=f"balance_{i}")
        elif i == 6:
            # Demand node: net inflow = demand_node6
            model.addConstr(inflow - outflow == demand_node6, name=f"balance_{i}")
        else:
            # Intermediate nodes: flow balance
            model.addConstr(outflow - inflow == 0, name=f"balance_{i}")

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