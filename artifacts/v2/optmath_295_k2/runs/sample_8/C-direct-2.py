import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = 8
    cost = params["cost"]
    source_balance = params["net_outflow_node_0"]
    sink_balance = params["net_inflow_node_7"]

    def cost_position(i, j):
        return i * (n - 1) + (j if j < i else j - 1)

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = gp.Model("delivery_routing")
    model.setParam("OutputFlag", 0)

    flow = {}
    for i, j in arcs:
        flow[i, j] = model.addVar(vtype=GRB.BINARY, name=f"flow_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost[cost_position(i, j)] * flow[i, j] for i, j in arcs),
        GRB.MINIMIZE,
    )

    for k in range(n):
        if k == 0:
            rhs = source_balance
        elif k == n - 1:
            rhs = -sink_balance
        else:
            rhs = 0.0
        model.addConstr(
            gp.quicksum(flow[k, j] for j in range(n) if j != k)
            - gp.quicksum(flow[i, k] for i in range(n) if i != k)
            == rhs,
            name=f"balance_{k}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"status_{model.status}"}