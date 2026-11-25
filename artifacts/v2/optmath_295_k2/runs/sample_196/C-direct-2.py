import gurobipy as gp
from gurobipy import GRB


def solve(params):
    truck_capacity = params["truck_capacity"]
    good_weights = params["good_weights"]

    num_goods = len(good_weights)
    # At most one truck per good is enough; trucks are identical.
    num_trucks = num_goods

    model = gp.Model("truck_assignment")
    model.Params.OutputFlag = 0

    # x[i, j] = 1 if good i is assigned to truck j
    x = model.addVars(num_goods, num_trucks, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if truck j is used
    y = model.addVars(num_trucks, vtype=GRB.BINARY, name="y")

    # Assignment: each good goes to exactly one truck.
    for i in range(num_goods):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_trucks)) == 1,
            name=f"assign_{i}",
        )

    # Capacity: total weight on a used truck cannot exceed its capacity.
    # When y[j] = 0, the RHS is 0 and positive weights force all x[i, j] = 0.
    for j in range(num_trucks):
        model.addConstr(
            gp.quicksum(good_weights[i] * x[i, j] for i in range(num_goods))
            <= truck_capacity * y[j],
            name=f"cap_{j}",
        )

    # Symmetry breaking: identical trucks are used in index order.
    for j in range(num_trucks - 1):
        model.addConstr(y[j] >= y[j + 1], name=f"order_{j}")

    # Objective: minimize number of trucks used.
    model.setObjective(gp.quicksum(y[j] for j in range(num_trucks)), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"gurobi_status_{model.status}"}