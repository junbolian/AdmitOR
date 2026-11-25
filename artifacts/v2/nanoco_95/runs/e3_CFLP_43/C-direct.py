import gurobipy as gp
from gurobipy import GRB


def solve(params):
    installation_cost = params["installation_cost"]
    volume_capacity = params["volume_capacity"]
    customer_demand = params["customer_demand"]
    delivery_cost_matrix = params["delivery_cost_matrix"]
    # Coordinates are provided but the problem uses a precomputed delivery cost matrix,
    # so coordinates are not needed for the optimization model itself.
    # locker_coordinates_x = params["locker_coordinates_x"]
    # locker_coordinates_y = params["locker_coordinates_y"]
    # customer_coordinates_x = params["customer_coordinates_x"]
    # customer_coordinates_y = params["customer_coordinates_y"]

    num_customers = len(customer_demand)        # 15
    num_lockers = len(installation_cost)        # 6

    customers = range(num_customers)
    lockers = range(num_lockers)

    model = gp.Model("locker_network")
    model.Params.OutputFlag = 0

    # Activation variables: y[j] = 1 if locker j is activated
    y = model.addVars(lockers, vtype=GRB.BINARY, name="y")

    # Assignment variables: x[i,j] = 1 if customer i is assigned to locker j
    x = model.addVars(customers, lockers, vtype=GRB.BINARY, name="x")

    # Objective: fixed installation costs + last-mile delivery costs
    install_term = gp.quicksum(installation_cost[j] * y[j] for j in lockers)
    delivery_term = gp.quicksum(
        delivery_cost_matrix[i][j] * x[i, j]
        for i in customers
        for j in lockers
    )
    model.setObjective(install_term + delivery_term, GRB.MINIMIZE)

    # Each customer must be served by exactly one locker (single sourcing, no splitting)
    for i in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in lockers) == 1,
            name=f"single_source_{i}",
        )

    # Capacity constraints: assigned volume cannot exceed locker capacity,
    # and only active lockers can receive assignments.
    for j in lockers:
        model.addConstr(
            gp.quicksum(customer_demand[i] * x[i, j] for i in customers)
            <= volume_capacity[j] * y[j],
            name=f"capacity_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": f"status_{model.status}"}