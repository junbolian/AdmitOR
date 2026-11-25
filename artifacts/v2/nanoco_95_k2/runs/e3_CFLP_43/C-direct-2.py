import gurobipy as gp
from gurobipy import GRB


def solve(params):
    locker_fixed_costs = params["locker_fixed_costs"]
    locker_capacities = params["locker_capacities"]
    customer_demands = params["customer_demands"]
    delivery_cost_matrix = params["delivery_cost_matrix"]
    num_lockers = params["num_lockers"]
    num_customers = params["num_customers"]

    model = gp.Model("locker_network")

    y = model.addVars(num_lockers, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_customers, num_lockers, vtype=GRB.BINARY, name="x")

    fixed_cost = gp.quicksum(
        locker_fixed_costs[j] * y[j] for j in range(num_lockers)
    )
    delivery_cost = gp.quicksum(
        delivery_cost_matrix[i][j] * x[i, j]
        for i in range(num_customers)
        for j in range(num_lockers)
    )
    model.setObjective(fixed_cost + delivery_cost, GRB.MINIMIZE)

    for i in range(num_customers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_lockers)) == 1,
            name=f"assign_{i}",
        )

    for j in range(num_lockers):
        model.addConstr(
            gp.quicksum(
                customer_demands[i] * x[i, j] for i in range(num_customers)
            )
            <= locker_capacities[j] * y[j],
            name=f"capacity_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}