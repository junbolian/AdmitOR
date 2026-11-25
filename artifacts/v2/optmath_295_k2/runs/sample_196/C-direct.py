import gurobipy as gp
from gurobipy import GRB


def solve(params):
    truck_capacity = params["truck_capacity"]
    good_weights = params["good_weights"]

    n_goods = len(good_weights)
    n_trucks = n_goods  # upper bound: one truck per good is always feasible

    model = gp.Model("truck_assignment")
    model.Params.OutputFlag = 0

    # x[i, j] = 1 if good i is assigned to truck j
    x = model.addVars(n_goods, n_trucks, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if truck j is used
    y = model.addVars(n_trucks, vtype=GRB.BINARY, name="y")

    # Each good assigned to exactly one truck
    for i in range(n_goods):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_trucks)) == 1,
            name=f"assign_{i}",
        )

    # Capacity: total weight on truck j cannot exceed capacity, and only if used
    for j in range(n_trucks):
        model.addConstr(
            gp.quicksum(good_weights[i] * x[i, j] for i in range(n_goods))
            <= truck_capacity * y[j],
            name=f"cap_{j}",
        )

    # Minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in range(n_trucks)), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}