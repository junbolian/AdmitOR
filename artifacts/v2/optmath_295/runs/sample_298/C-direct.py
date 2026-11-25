import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Extract parameters
    supply_node0 = params["supply_node0"]
    demand_node9 = params["demand_node9"]

    # Build cost dictionary for all arcs
    costs = {}
    arc_keys = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9),
        (1,0),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),
    ]
    for (i, j) in arc_keys:
        costs[(i, j)] = params[f"cost_{i}_{j}"]

    nodes = list(range(10))

    model = gp.Model("min_cost_flow")
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(arc_keys, vtype=GRB.BINARY, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(costs[(i, j)] * x[(i, j)] for (i, j) in arc_keys),
        GRB.MINIMIZE
    )

    # Supply constraint: node_0 sends out supply_node0
    out_0 = [j for (i, j) in arc_keys if i == 0]
    in_0  = [i for (i, j) in arc_keys if j == 0]
    model.addConstr(
        gp.quicksum(x[(0, j)] for j in out_0) -
        gp.quicksum(x[(i, 0)] for i in in_0) == supply_node0,
        name="supply_node0"
    )

    # Demand constraint: node_9 receives demand_node9
    in_9  = [i for (i, j) in arc_keys if j == 9]
    out_9 = [j for (i, j) in arc_keys if i == 9]
    model.addConstr(
        gp.quicksum(x[(i, 9)] for i in in_9) -
        gp.quicksum(x[(9, j)] for j in out_9) == demand_node9,
        name="demand_node9"
    )

    # Flow conservation for intermediate nodes 1..8
    for node in range(1, 9):
        in_arcs  = [i for (i, j) in arc_keys if j == node]
        out_arcs = [j for (i, j) in arc_keys if i == node]
        model.addConstr(
            gp.quicksum(x[(i, node)] for i in in_arcs) ==
            gp.quicksum(x[(node, j)] for j in out_arcs),
            name=f"flow_conservation_{node}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}