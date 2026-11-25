import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nodes = list(range(6))

    # Build cost dictionary from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    # Create model
    model = gp.Model("logistics_network")
    model.Params.OutputFlag = 0

    # Binary decision variables: x[i, j] = 1 if route i->j is used, 0 otherwise
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Flow balance constraints
    for k in nodes:
        outflow = gp.quicksum(x[k, j] for j in nodes if j != k)
        inflow = gp.quicksum(x[i, k] for i in nodes if i != k)

        if k == 0:
            # Supply node: outflow - inflow = supply
            model.addConstr(outflow - inflow == params["supply_node0"], name=f"balance_{k}")
        elif k == 5:
            # Demand node: inflow - outflow = demand
            model.addConstr(inflow - outflow == params["demand_node5"], name=f"balance_{k}")
        else:
            # Transshipment node: outflow = inflow
            model.addConstr(outflow - inflow == 0, name=f"balance_{k}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}