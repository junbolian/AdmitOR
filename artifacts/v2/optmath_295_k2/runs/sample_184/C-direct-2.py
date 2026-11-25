import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply   = params["supply"]
    demand   = params["demand"]
    cost     = params["cost"]
    capacity = params["capacity"]

    num_origins = 4
    num_destinations = 5
    num_products = 2

    origins = range(num_origins)
    destinations = range(num_destinations)
    products = range(num_products)

    def _flat(data):
        try:
            len(data[0])
            return False
        except TypeError:
            return True

    flat_s = _flat(supply)
    flat_d = _flat(demand)
    flat_c = _flat(cost)
    flat_cap = _flat(capacity)

    def s(i, p):
        return supply[i][p] if not flat_s else supply[i * num_products + p]

    def d(j, p):
        return demand[j][p] if not flat_d else demand[j * num_products + p]

    def c(i, j, p):
        if not flat_c:
            return cost[i][j][p]
        return cost[i * num_destinations * num_products + j * num_products + p]

    def cap(i, j):
        return capacity[i][j] if not flat_cap else capacity[i * num_destinations + j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, destinations, products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(c(i, j, p) * x[i, j, p]
                    for i in origins
                    for j in destinations
                    for p in products),
        GRB.MINIMIZE
    )

    for i in origins:
        for p in products:
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in destinations) == s(i, p),
                name=f"supply_{i}_{p}"
            )

    for j in destinations:
        for p in products:
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in origins) == d(j, p),
                name=f"demand_{j}_{p}"
            )

    for i in origins:
        for j in destinations:
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in products) <= cap(i, j),
                name=f"capacity_{i}_{j}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}