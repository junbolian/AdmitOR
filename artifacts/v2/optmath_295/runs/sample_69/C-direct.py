import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }

    u_lb = params["u_bound_lower"]
    u_ub = params["u_bound_upper"]
    u0_fixed = params["u_city0"]

    n = 4
    cities = list(range(n))
    arcs = list(cost.keys())

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Position variables: u[0] fixed, u[1..3] bounded
    u = {}
    u[0] = model.addVar(lb=u0_fixed, ub=u0_fixed, vtype=GRB.CONTINUOUS, name="u_0")
    for i in [1, 2, 3]:
        u[i] = model.addVar(lb=u_lb, ub=u_ub, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective
    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)

    # Each city visited exactly once (one incoming arc)
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if (i, j) in cost) == 1,
            name=f"visit_{j}"
        )

    # Each city departed exactly once (one outgoing arc)
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if (i, j) in cost) == 1,
            name=f"depart_{i}"
        )

    # Miller-Tucker-Zemlin subtour elimination for non-depot cities
    big_m = n - 1  # positions range 0..n-1, so difference <= n-1
    for i in [1, 2, 3]:
        for j in [1, 2, 3]:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + big_m * x[i, j] <= big_m - 1,
                    name=f"mtz_{i}_{j}"
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