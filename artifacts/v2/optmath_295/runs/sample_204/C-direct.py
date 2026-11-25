import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = {
        0: params["supply_0"],
        1: params["supply_1"],
    }
    demand = {
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    nodes = list(range(6))
    # All directed arcs (no self-loops)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {
        (i, j): params[f"cost_{i}_to_{j}"]
        for (i, j) in arcs
    }
    cap = {
        (i, j): params[f"cap_{i}_to_{j}"]
        for (i, j) in arcs
    }

    # Net supply: positive = surplus, negative = demand
    net = {}
    for nd in nodes:
        if nd in supply:
            net[nd] = supply[nd]
        elif nd in demand:
            net[nd] = -demand[nd]
        else:
            net[nd] = 0.0

    model = gp.Model("emergency_supply")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, lb=0.0, name="x")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(x[i, j] <= cap[i, j], name=f"cap_{i}_{j}")

    # Flow balance: outflow - inflow = net supply
    for nd in nodes:
        outflow = gp.quicksum(x[nd, j] for j in nodes if j != nd)
        inflow  = gp.quicksum(x[i, nd] for i in nodes if i != nd)
        model.addConstr(outflow - inflow == net[nd], name=f"balance_{nd}")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}