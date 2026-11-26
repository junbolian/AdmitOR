import gurobipy as gp
from gurobipy import GRB


def solve(params):
    volume = params["volume"]
    demand = params["demand"]
    unit_cost = params["unit_cost"]
    setup_cost = params["setup_cost"]

    n = len(volume)

    model = gp.Model("red_star_plastics")
    model.Params.OutputFlag = 0

    # Production quantity of each container type
    x = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="x")
    # Equipment activation indicator
    y = model.addVars(n, vtype=GRB.BINARY, name="y")
    # s[j, i] = units of type j (volume >= type i) used to satisfy demand of type i
    s = model.addVars(n, n, lb=0.0, vtype=GRB.CONTINUOUS, name="s")

    # Substitution allowed only from equal-or-larger volume types
    for j in range(n):
        for i in range(n):
            if volume[j] < volume[i]:
                s[j, i].ub = 0.0

    # Demand of each type fully met by itself or larger-volume substitutes
    for i in range(n):
        model.addConstr(
            gp.quicksum(s[j, i] for j in range(n)) >= demand[i],
            name=f"demand_{i}",
        )

    # Substitutions cannot exceed production of each type
    for j in range(n):
        model.addConstr(
            gp.quicksum(s[j, i] for i in range(n)) <= x[j],
            name=f"link_sub_{j}",
        )

    # Production requires activation; big-M is the total demand
    # that could plausibly be served by type j (its own or smaller-volume demands)
    bigM = [sum(demand[i] for i in range(n) if volume[i] <= volume[j]) for j in range(n)]
    for j in range(n):
        model.addConstr(x[j] <= bigM[j] * y[j], name=f"link_y_{j}")

    # Objective: variable production costs + fixed setup costs
    model.setObjective(
        gp.quicksum(unit_cost[j] * x[j] for j in range(n))
        + setup_cost * gp.quicksum(y[j] for j in range(n)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}