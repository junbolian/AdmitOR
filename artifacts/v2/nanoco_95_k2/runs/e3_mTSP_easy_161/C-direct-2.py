import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    n_nodes = len(distance_matrix)
    n_customers = n_nodes - 1  # nodes 1..8
    customers = list(range(1, n_nodes))
    all_nodes = list(range(n_nodes))
    vehicles = list(range(num_vehicles))

    # Cost matrix
    c = {(i, j): distance_matrix[i][j] for i in all_nodes for j in all_nodes}

    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j,k] = 1 if vehicle k travels from node i to node j
    x = model.addVars(
        [(i, j, k) for i in all_nodes for j in all_nodes for k in vehicles if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(c[i, j] * x[i, j, k] for i in all_nodes for j in all_nodes for k in vehicles if i != j),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in all_nodes for k in vehicles if i != j) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation at each customer for each vehicle
    for k in vehicles:
        for h in customers:
            model.addConstr(
                gp.quicksum(x[i, h, k] for i in all_nodes if i != h) ==
                gp.quicksum(x[h, j, k] for j in all_nodes if j != h),
                name=f"flow_{h}_{k}"
            )

    # Each vehicle departs depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in customers) == 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[i, 0, k] for i in customers) == 1,
            name=f"return_{k}"
        )

    # Subtour elimination via MTZ formulation
    # u[i,k]: position of node i in vehicle k's route (only for customers)
    u = model.addVars(
        [(i, k) for i in customers for k in vehicles],
        lb=1.0, ub=float(n_customers),
        vtype=GRB.CONTINUOUS,
        name="u"
    )

    for k in vehicles:
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + n_customers * x[i, j, k] <= n_customers - 1,
                        name=f"mtz_{i}_{j}_{k}"
                    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj_val = model.ObjVal
        stat_str = "optimal" if status == GRB.OPTIMAL else "time_limit_feasible"
        return {"objective": obj_val, "status": stat_str}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}