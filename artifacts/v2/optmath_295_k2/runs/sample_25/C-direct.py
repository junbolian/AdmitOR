import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_0_1 = params["cost_0_1"]
    cost_0_2 = params["cost_0_2"]
    cost_0_3 = params["cost_0_3"]
    cost_1_0 = params["cost_1_0"]
    cost_1_2 = params["cost_1_2"]
    cost_1_3 = params["cost_1_3"]
    cost_2_0 = params["cost_2_0"]
    cost_2_1 = params["cost_2_1"]
    cost_2_3 = params["cost_2_3"]
    cost_3_0 = params["cost_3_0"]
    cost_3_1 = params["cost_3_1"]
    cost_3_2 = params["cost_3_2"]
    n_cities = params["n_cities"]
    position_city_0 = params["position_city_0"]
    position_lower_bound = params["position_lower_bound"]
    position_upper_bound = params["position_upper_bound"]
    mtz_big_M = params["mtz_big_M"]
    mtz_rhs = params["mtz_rhs"]

    cities = list(range(n_cities))  # [0, 1, 2, 3]

    # Cost matrix indexed by (i, j) for i != j
    cost = {
        (0, 1): cost_0_1, (0, 2): cost_0_2, (0, 3): cost_0_3,
        (1, 0): cost_1_0, (1, 2): cost_1_2, (1, 3): cost_1_3,
        (2, 0): cost_2_0, (2, 1): cost_2_1, (2, 3): cost_2_3,
        (3, 0): cost_3_0, (3, 1): cost_3_1, (3, 2): cost_3_2,
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Position variables: u[0] fixed, u[1..3] integer in [lb, ub]
    u = {}
    u[0] = model.addVar(lb=position_city_0, ub=position_city_0,
                        vtype=GRB.CONTINUOUS, name="u_0")
    for i in [1, 2, 3]:
        u[i] = model.addVar(lb=position_lower_bound, ub=position_upper_bound,
                            vtype=GRB.INTEGER, name=f"u_{i}")

    model.update()

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
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

    # MTZ subtour elimination: for all i != j, both not 0
    # mtz_big_M * x[i,j] + u[i] - u[j] <= mtz_rhs
    non_depot_pairs = [(i, j) for i in [1, 2, 3] for j in [1, 2, 3] if i != j]
    for (i, j) in non_depot_pairs:
        model.addConstr(
            mtz_big_M * x[i, j] + u[i] - u[j] <= mtz_rhs,
            name=f"mtz_{i}_{j}"
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