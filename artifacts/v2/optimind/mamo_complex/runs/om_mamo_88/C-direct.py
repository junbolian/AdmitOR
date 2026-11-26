def solve(params):
    import gurobipy as gp
    from gurobipy import GRB

    initial_stock = params["initial_stock"]
    required_demand = params["required_demand"]

    # Build cost matrix: cost[i][j] for i != j (0-indexed)
    cost = {}
    cost[(0, 1)] = params["transport_cost_1_to_2"]
    cost[(0, 2)] = params["transport_cost_1_to_3"]
    cost[(0, 3)] = params["transport_cost_1_to_4"]
    cost[(1, 0)] = params["transport_cost_2_to_1"]
    cost[(1, 2)] = params["transport_cost_2_to_3"]
    cost[(1, 3)] = params["transport_cost_2_to_4"]
    cost[(2, 0)] = params["transport_cost_3_to_1"]
    cost[(2, 1)] = params["transport_cost_3_to_2"]
    cost[(2, 3)] = params["transport_cost_3_to_4"]
    cost[(3, 0)] = params["transport_cost_4_to_1"]
    cost[(3, 1)] = params["transport_cost_4_to_2"]
    cost[(3, 2)] = params["transport_cost_4_to_3"]

    clinics = [0, 1, 2, 3]
    arcs = [(i, j) for i in clinics for j in clinics if i != j]

    model = gp.Model("clinic_supply")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow from clinic i to clinic j
    x = model.addVars(arcs, lb=0.0, name="x")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints:
    # initial_stock[i] + inflow[i] - outflow[i] >= required_demand[i]
    for i in clinics:
        inflow = gp.quicksum(x[j, i] for j in clinics if j != i)
        outflow = gp.quicksum(x[i, j] for j in clinics if j != i)
        model.addConstr(
            initial_stock[i] + inflow - outflow >= required_demand[i],
            name=f"balance_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}