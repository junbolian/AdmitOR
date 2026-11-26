import gurobipy as gp
from gurobipy import GRB

def solve(params):
    wage_skilled = params["wage_skilled"]
    wage_laborer = params["wage_laborer"]
    eff_skilled = params["eff_hours_skilled"]
    eff_laborer = params["eff_hours_laborer"]
    demand1 = params["demand_task1"]
    demand2 = params["demand_task2"]
    demand3 = params["demand_task3"]
    max_skilled = params["max_skilled"]
    max_laborers = params["max_laborers"]

    model = gp.Model("workforce")
    model.setParam("OutputFlag", 0)

    # Task 1: x1a = skilled workers alone, x1b = teams of (1 skilled + 2 laborers)
    x1a = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x1a")
    x1b = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x1b")

    # Task 2: x2a = skilled workers alone, x2b = laborers alone
    x2a = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x2a")
    x2b = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x2b")

    # Task 3: x3a = teams of 5 laborers, x3b = teams of (1 skilled + 3 laborers)
    x3a = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x3a")
    x3b = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x3b")

    # Effective hours per team/worker contributed to each task:
    # Task 1 mode A: 1 skilled worker → eff_skilled hours each
    # Task 1 mode B: 1 skilled + 2 laborers → eff_skilled + 2*eff_laborer hours per team
    # Task 2 mode A: 1 skilled → eff_skilled hours each
    # Task 2 mode B: 1 laborer → eff_laborer hours each
    # Task 3 mode A: 5 laborers → 5*eff_laborer hours per team
    # Task 3 mode B: 1 skilled + 3 laborers → eff_skilled + 3*eff_laborer hours per team

    model.addConstr(
        x1a * eff_skilled + x1b * (eff_skilled + 2 * eff_laborer) >= demand1,
        name="demand_task1"
    )
    model.addConstr(
        x2a * eff_skilled + x2b * eff_laborer >= demand2,
        name="demand_task2"
    )
    model.addConstr(
        x3a * (5 * eff_laborer) + x3b * (eff_skilled + 3 * eff_laborer) >= demand3,
        name="demand_task3"
    )

    # Total skilled workers
    total_skilled = x1a + x1b + x2a + x3b
    model.addConstr(total_skilled <= max_skilled, name="cap_skilled")

    # Total laborers
    total_laborers = 2 * x1b + x2b + 5 * x3a + 3 * x3b
    model.addConstr(total_laborers <= max_laborers, name="cap_laborers")

    # Objective: minimize total weekly wage
    model.setObjective(
        total_skilled * wage_skilled + total_laborers * wage_laborer,
        GRB.MINIMIZE
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