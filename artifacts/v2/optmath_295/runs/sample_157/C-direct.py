import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_node0 = params["supply_node0"]
    demand_node5 = params["demand_node5"]

    # Build cost dict from params
    arcs = [
        (0,1),(0,2),(0,3),(0,4),(0,5),
        (1,0),(1,2),(1,3),(1,4),(1,5),
        (2,0),(2,1),(2,3),(2,4),(2,5),
        (3,0),(3,1),(3,2),(3,4),(3,5),
        (4,0),(4,1),(4,2),(4,3),(4,5),
        (5,0),(5,1),(5,2),(5,3),(5,4),
    ]

    cost = {
        (i, j): params[f"cost_{i}_{j}"]
        for (i, j) in arcs
    }

    nodes = list(range(6))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[a] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for node in nodes:
        outflow = gp.quicksum(x[i, j] for (i, j) in arcs if i == node)
        inflow  = gp.quicksum(x[i, j] for (i, j) in arcs if j == node)

        if node == 0:
            # Supply node: outflow - inflow = supply
            model.addConstr(outflow - inflow == supply_node0, name=f"balance_{node}")
        elif node == 5:
            # Demand node: inflow - outflow = demand
            model.addConstr(inflow - outflow == demand_node5, name=f"balance_{node}")
        else:
            # Transshipment: inflow == outflow
            model.addConstr(inflow - outflow == 0, name=f"balance_{node}")

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