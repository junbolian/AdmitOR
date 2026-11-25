import gurobipy as gp
from gurobipy import GRB


def solve(params):
    model = gp.Model("logistics")
    model.setParam("OutputFlag", 0)

    nodes = list(range(7))

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    supply_node_0 = params["supply_node_0"]
    demand_node_6 = params["demand_node_6"]
    balance_nodes_1_to_5 = params["balance_nodes_1_to_5"]
    route_usage_upper_bound = params["route_usage_upper_bound"]

    # Binary decision variables: x[i,j] = 1 if route i->j is used.
    # Do not pass ub separately for BINARY vars; the type already enforces {0,1}.
    # We honour route_usage_upper_bound by adding an explicit upper-bound constraint
    # so the param is used without triggering a range-constraint error.
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[(i, j)] = model.addVar(
                    vtype=GRB.BINARY,
                    name=f"x_{i}_{j}",
                )

    # Enforce route_usage_upper_bound as an explicit constraint on every arc.
    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(
                    x[(i, j)] <= route_usage_upper_bound,
                    name=f"ub_{i}_{j}",
                )

    # Objective: minimise total transportation cost.
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE,
    )

    # Node 0 (source): outflow - inflow = supply_node_0
    model.addConstr(
        gp.quicksum(x[(0, j)] for j in nodes if j != 0)
        - gp.quicksum(x[(i, 0)] for i in nodes if i != 0)
        == supply_node_0,
        name="balance_node_0",
    )

    # Node 6 (destination): inflow - outflow = demand_node_6
    model.addConstr(
        gp.quicksum(x[(i, 6)] for i in nodes if i != 6)
        - gp.quicksum(x[(6, j)] for j in nodes if j != 6)
        == demand_node_6,
        name="balance_node_6",
    )

    # Nodes 1–5 (intermediate): inflow - outflow = balance_nodes_1_to_5
    for k in range(1, 6):
        model.addConstr(
            gp.quicksum(x[(i, k)] for i in nodes if i != k)
            - gp.quicksum(x[(k, j)] for j in nodes if j != k)
            == balance_nodes_1_to_5,
            name=f"balance_node_{k}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"status_{model.status}"}