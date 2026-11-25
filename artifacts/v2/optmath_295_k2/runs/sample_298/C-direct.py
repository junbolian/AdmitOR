import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = {}
    costs[(0,1)] = params["cost_node0_to_node1"]
    costs[(0,2)] = params["cost_node0_to_node2"]
    costs[(0,3)] = params["cost_node0_to_node3"]
    costs[(0,4)] = params["cost_node0_to_node4"]
    costs[(0,5)] = params["cost_node0_to_node5"]
    costs[(0,6)] = params["cost_node0_to_node6"]
    costs[(0,7)] = params["cost_node0_to_node7"]
    costs[(0,8)] = params["cost_node0_to_node8"]
    costs[(0,9)] = params["cost_node0_to_node9"]
    costs[(1,0)] = params["cost_node1_to_node0"]
    costs[(1,2)] = params["cost_node1_to_node2"]
    costs[(1,3)] = params["cost_node1_to_node3"]
    costs[(1,4)] = params["cost_node1_to_node4"]
    costs[(1,5)] = params["cost_node1_to_node5"]
    costs[(1,6)] = params["cost_node1_to_node6"]
    costs[(1,7)] = params["cost_node1_to_node7"]
    costs[(1,8)] = params["cost_node1_to_node8"]
    costs[(1,9)] = params["cost_node1_to_node9"]

    arcs = list(costs.keys())

    # Net supply at each node: positive = supply (outflow > inflow), negative = demand
    supply_node = {}
    supply_node[0] = params["supply_node0"]
    supply_node[9] = -params["demand_node9"]
    intermediate_net = params["intermediate_net_flow"]
    for i in range(1, 9):
        supply_node[i] = intermediate_net

    model = gp.Model("min_cost_flow")
    model.setParam("OutputFlag", 0)

    x = {}
    for (i, j) in arcs:
        x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(costs[(i, j)] * x[(i, j)] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    for node in range(10):
        out_arcs = [(i, j) for (i, j) in arcs if i == node]
        in_arcs  = [(i, j) for (i, j) in arcs if j == node]

        lhs = gp.LinExpr()
        for (i, j) in out_arcs:
            lhs += x[(i, j)]
        for (i, j) in in_arcs:
            lhs -= x[(i, j)]

        rhs = supply_node.get(node, intermediate_net)

        # Only add constraint if lhs contains variables; otherwise check feasibility
        if len(out_arcs) == 0 and len(in_arcs) == 0:
            if abs(rhs) > 1e-9:
                return {"objective": None, "status": "infeasible"}
        else:
            model.addConstr(lhs == rhs, name=f"flow_conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}