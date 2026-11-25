import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_R0_S0 = params["demand_R0_S0"]
    demand_R0_S1 = params["demand_R0_S1"]
    demand_R1_S0 = params["demand_R1_S0"]
    demand_R1_S1 = params["demand_R1_S1"]
    pref_cost_emp1 = params["pref_cost_emp1"]
    pref_cost_emp2 = params["pref_cost_emp2"]
    pref_cost_emp3 = params["pref_cost_emp3"]
    pref_cost_emp4 = params["pref_cost_emp4"]
    penalty_per_unfulfilled = params["penalty_per_unfulfilled"]

    restaurants = [0, 1]
    shifts = [0, 1]
    skill0_employees = [1, 2, 3, 4]

    # Employee availability by shift (only Skill 0 employees matter;
    # E0 and E5 lack Skill 0 and can never be assigned)
    availability = {
        1: {0, 1},
        2: {0, 1},
        3: {0},      # unavailable for Shift 1
        4: {0, 1},
    }

    pref_cost = {
        1: pref_cost_emp1,
        2: pref_cost_emp2,
        3: pref_cost_emp3,
        4: pref_cost_emp4,
    }

    demand = {
        (0, 0): demand_R0_S0,
        (0, 1): demand_R0_S1,
        (1, 0): demand_R1_S0,
        (1, 1): demand_R1_S1,
    }

    model = gp.Model("staffing")
    model.Params.OutputFlag = 0

    # Assignment variables: x[e, r, s] = 1 if employee e works restaurant r, shift s
    x = {}
    for e in skill0_employees:
        for r in restaurants:
            for s in shifts:
                if s in availability[e]:
                    x[e, r, s] = model.addVar(vtype=GRB.BINARY, name=f"x_{e}_{r}_{s}")

    # Unfulfilled-position variables
    u = {}
    for r in restaurants:
        for s in shifts:
            u[r, s] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"u_{r}_{s}")

    model.update()

    # Objective: minimize preference costs + penalty for unfulfilled positions
    obj = gp.LinExpr()
    for (e, r, s), var in x.items():
        obj += pref_cost[e] * var
    for r in restaurants:
        for s in shifts:
            obj += penalty_per_unfulfilled * u[r, s]
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand fulfillment: assigned + unfulfilled = demand
    for r in restaurants:
        for s in shifts:
            assigned = gp.quicksum(
                x[e, r, s] for e in skill0_employees if (e, r, s) in x
            )
            model.addConstr(assigned + u[r, s] == demand[r, s], name=f"demand_{r}_{s}")

    # Each employee assigned to at most one shift across all restaurants
    for e in skill0_employees:
        total = gp.quicksum(
            x[e, r, s] for r in restaurants for s in shifts if (e, r, s) in x
        )
        model.addConstr(total <= 1, name=f"one_shift_{e}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}