import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_R0_S0 = params["demand_R0_S0"]
    demand_R0_S1 = params["demand_R0_S1"]
    demand_R1_S0 = params["demand_R1_S0"]
    demand_R1_S1 = params["demand_R1_S1"]
    pref_cost_E1 = params["pref_cost_E1"]
    pref_cost_E2 = params["pref_cost_E2"]
    pref_cost_E3 = params["pref_cost_E3"]
    pref_cost_E4 = params["pref_cost_E4"]
    penalty = params["penalty"]

    # Employees: 0..5
    # Skill-0 employees: 1, 2, 3, 4
    # Availability: E0 unavailable all; E1,2,4,5 available both shifts; E3 available shift 0 only
    # Only skill-0 employees can be assigned (E0, E5 cannot)

    # Preference costs indexed by employee
    pref_costs = {
        1: pref_cost_E1,
        2: pref_cost_E2,
        3: pref_cost_E3,
        4: pref_cost_E4,
    }

    # (restaurant, shift) -> demand
    demand = {
        (0, 0): demand_R0_S0,
        (0, 1): demand_R0_S1,
        (1, 0): demand_R1_S0,
        (1, 1): demand_R1_S1,
    }

    # Valid (employee, restaurant, shift) assignments
    # Only employees with skill 0: 1, 2, 3, 4
    # Availability: E3 only shift 0; others (1,2,4) both shifts
    valid_assignments = []
    for r in [0, 1]:
        for s in [0, 1]:
            for e in [1, 2, 3, 4]:
                if e == 3 and s == 1:
                    continue  # E3 unavailable for shift 1
                valid_assignments.append((e, r, s))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = model.addVars(valid_assignments, vtype=GRB.BINARY, name="x")

    # Unfulfilled (slack) variables for each (restaurant, shift)
    u = model.addVars([(r, s) for r in [0, 1] for s in [0, 1]],
                      vtype=GRB.CONTINUOUS, lb=0.0, name="u")

    # Objective: preference costs + penalty for unfulfilled
    obj = gp.quicksum(pref_costs[e] * x[e, r, s] for (e, r, s) in valid_assignments)
    obj += gp.quicksum(penalty * u[r, s] for r in [0, 1] for s in [0, 1])
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand constraints: assigned + unfulfilled = demand
    for r in [0, 1]:
        for s in [0, 1]:
            assigned = gp.quicksum(
                x[e, r, s] for (e, rr, ss) in valid_assignments if rr == r and ss == s
            )
            model.addConstr(assigned + u[r, s] == demand[r, s], name=f"demand_R{r}_S{s}")

    # Each employee assigned to at most one shift across all restaurants
    for e in [1, 2, 3, 4]:
        emp_assignments = [(ee, r, s) for (ee, r, s) in valid_assignments if ee == e]
        if emp_assignments:
            model.addConstr(gp.quicksum(x[ee, r, s] for (ee, r, s) in emp_assignments) <= 1,
                            name=f"one_shift_E{e}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}