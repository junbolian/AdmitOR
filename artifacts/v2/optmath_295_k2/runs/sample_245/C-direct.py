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
    # Availability: E0 unavailable both shifts, E1 both, E2 both, E3 shift0 only, E4 both, E5 both
    # But E0 and E5 lack Skill 0, so cannot be assigned to any shift (all shifts require skill 0)

    # Preference costs indexed by employee
    pref_cost = {
        0: 0,           # irrelevant, E0 can't be assigned
        1: pref_cost_E1,
        2: pref_cost_E2,
        3: pref_cost_E3,
        4: pref_cost_E4,
        5: 0,           # irrelevant, E5 can't be assigned
    }

    # Restaurants: 0, 1
    # Shifts: 0, 1
    # demand[r][s]
    demand = {
        0: {0: demand_R0_S0, 1: demand_R0_S1},
        1: {0: demand_R1_S0, 1: demand_R1_S1},
    }

    # Feasible (employee, restaurant, shift) combinations
    # Only employees with Skill 0 and available for the shift
    # Skill 0 employees: 1, 2, 3, 4
    # Availability:
    #   E1: shifts 0, 1
    #   E2: shifts 0, 1
    #   E3: shift 0 only
    #   E4: shifts 0, 1
    employee_availability = {
        1: [0, 1],
        2: [0, 1],
        3: [0],
        4: [0, 1],
    }

    # Build valid assignments
    valid_assignments = []
    for e, avail_shifts in employee_availability.items():
        for r in [0, 1]:
            for s in avail_shifts:
                valid_assignments.append((e, r, s))

    model = gp.Model("restaurant_scheduling")
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[e, r, s] = 1 if employee e assigned to restaurant r, shift s
    x = model.addVars(valid_assignments, vtype=GRB.BINARY, name="x")

    # Unfulfilled positions: u[r, s] >= 0
    u = model.addVars([0, 1], [0, 1], vtype=GRB.CONTINUOUS, lb=0.0, name="u")

    # Objective: minimize preference costs + penalty costs
    obj = gp.LinExpr()
    for (e, r, s) in valid_assignments:
        obj += pref_cost[e] * x[e, r, s]
    for r in [0, 1]:
        for s in [0, 1]:
            obj += penalty * u[r, s]
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand constraints: sum of assigned employees + unfulfilled = demand
    for r in [0, 1]:
        for s in [0, 1]:
            assigned = gp.LinExpr()
            for (e, r2, s2) in valid_assignments:
                if r2 == r and s2 == s:
                    assigned += x[e, r2, s2]
            model.addConstr(assigned + u[r, s] == demand[r][s], name=f"demand_R{r}_S{s}")

    # Each employee assigned to at most one shift across all restaurants
    for e in employee_availability:
        all_assignments_for_e = [(e2, r, s) for (e2, r, s) in valid_assignments if e2 == e]
        if all_assignments_for_e:
            model.addConstr(
                gp.quicksum(x[e2, r, s] for (e2, r, s) in all_assignments_for_e) <= 1,
                name=f"one_shift_E{e}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}