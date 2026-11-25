import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    num_cities = params["num_cities"]
    pos_lb = params["position_lower_bound"]
    pos_ub = params["position_upper_bound"]
    start_city = params["start_city"]

    n = num_cities
    cities = list(range(n))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: x[i][j] = 1 if we travel from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Continuous variable: u[i] = position of city i in the tour
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # Fix start city position
    model.addConstr(u[start_city] == 0, name="start_pos")

    # MTZ subtour elimination constraints
    # For non-start cities i and j: u[i] - u[j] + n * x[i,j] <= n - 1
    for i in cities:
        for j in cities:
            if i != j and i != start_city and j != start_city:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )
            elif i != j and j == start_city and i != start_city:
                # Outgoing arcs to start city don't need subtour elimination
                pass
            elif i != j and i == start_city:
                # From start city: u[j] >= 1 when x[start,j] = 1
                model.addConstr(
                    u[j] >= x[i, j],
                    name=f"mtz_start_{i}_{j}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}