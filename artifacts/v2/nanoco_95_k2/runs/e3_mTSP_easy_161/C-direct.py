import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance = params["distance_matrix"]
    num_vehicles = int(params["num_vehicles"])

    n_nodes = len(distance)
    depot = 0
    customers = list(range(1, n_nodes))
    n_customers = len(customers)

    model = gp.Model("last_mile_vrp")
    model.setParam("OutputFlag", 0)

    arcs = [(i, j) for i in range(n_nodes) for j in range(n_nodes) if i != j]
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(distance[i][j] * x[i, j] for i, j in arcs),
        GRB.MINIMIZE,
    )

    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_nodes) if i != j) == 1,
            name=f"visit_in_{j}",
        )

    for i in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_nodes) if i != j) == 1,
            name=f"visit_out_{i}",
        )

    model.addConstr(
        gp.quicksum(x[depot, j] for j in customers) == num_vehicles,
        name="departures",
    )
    model.addConstr(
        gp.quicksum(x[i, depot] for i in customers) == num_vehicles,
        name="returns",
    )

    u = model.addVars(
        customers, lb=1.0, ub=n_customers, vtype=GRB.CONTINUOUS, name="u"
    )
    for i in customers:
        for j in customers:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n_customers * x[i, j] <= n_customers - 1,
                    name=f"mtz_{i}_{j}",
                )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"gurobi_status_{model.status}"}