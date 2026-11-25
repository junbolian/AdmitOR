import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    n_agents = 6
    n_tickets = 6

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_agents, n_tickets, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_agents) for j in range(n_tickets)),
        GRB.MINIMIZE
    )

    for i in range(n_agents):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_tickets)) == 1, name=f"agent_{i}")

    for j in range(n_tickets):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n_agents)) == 1, name=f"ticket_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}