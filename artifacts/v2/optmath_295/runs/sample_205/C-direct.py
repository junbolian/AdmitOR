import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_0_1 = params["cost_0_1"]
    cost_0_2 = params["cost_0_2"]
    cost_1_0 = params["cost_1_0"]
    cost_1_2 = params["cost_1_2"]
    cost_2_0 = params["cost_2_0"]
    cost_2_1 = params["cost_2_1"]
    position_lb_city1 = params["position_lb_city1"]
    position_ub_city1 = params["position_ub_city1"]
    position_lb_city2 = params["position_lb_city2"]
    position_ub_city2 = params["position_ub_city2"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route variables: x[i][j] = 1 if route from city i to city j is taken
    x_0_1 = model.addVar(vtype=GRB.BINARY, name="x_0_1")
    x_0_2 = model.addVar(vtype=GRB.BINARY, name="x_0_2")
    x_1_0 = model.addVar(vtype=GRB.BINARY, name="x_1_0")
    x_1_2 = model.addVar(vtype=GRB.BINARY, name="x_1_2")
    x_2_0 = model.addVar(vtype=GRB.BINARY, name="x_2_0")
    x_2_1 = model.addVar(vtype=GRB.BINARY, name="x_2_1")

    # Position variables for subtour elimination
    # City 0 is unrestricted (use large bounds)
    u0 = model.addVar(lb=-GRB.INFINITY, ub=GRB.INFINITY, name="u0")
    u1 = model.addVar(lb=position_lb_city1, ub=position_ub_city1, name="u1")
    u2 = model.addVar(lb=position_lb_city2, ub=position_ub_city2, name="u2")

    # Objective: minimize total travel cost
    model.setObjective(
        cost_0_1 * x_0_1 + cost_0_2 * x_0_2 +
        cost_1_0 * x_1_0 + cost_1_2 * x_1_2 +
        cost_2_0 * x_2_0 + cost_2_1 * x_2_1,
        GRB.MINIMIZE
    )

    # Each city visited exactly once (in-flow = 1)
    model.addConstr(x_1_0 + x_2_0 == 1, name="visit_city0")
    model.addConstr(x_0_1 + x_2_1 == 1, name="visit_city1")
    model.addConstr(x_0_2 + x_1_2 == 1, name="visit_city2")

    # Each city departed exactly once (out-flow = 1)
    model.addConstr(x_0_1 + x_0_2 == 1, name="depart_city0")
    model.addConstr(x_1_0 + x_1_2 == 1, name="depart_city1")
    model.addConstr(x_2_0 + x_2_1 == 1, name="depart_city2")

    # Subtour elimination: Miller-Tucker-Zemlin style constraints
    # Big-M for linearization; positions are bounded in [0,2], so M=2 suffices
    big_m = 2.0

    # If x_1_2 = 1 then u1 < u2, i.e., u1 - u2 <= -1 + M*(1 - x_1_2)
    model.addConstr(u1 - u2 <= -1 + big_m * (1 - x_1_2), name="subtour_1_2")

    # If x_2_1 = 1 then u2 < u1, i.e., u2 - u1 <= -1 + M*(1 - x_2_1)
    model.addConstr(u2 - u1 <= -1 + big_m * (1 - x_2_1), name="subtour_2_1")

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