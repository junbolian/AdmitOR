import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # ---- Read all numeric data from params ----
    wage_s = params["wage_skilled"]
    wage_l = params["wage_laborer"]
    h_s = params["effective_hours_skilled"]   # effective weekly hours per skilled worker
    h_l = params["effective_hours_laborer"]   # effective weekly hours per laborer
    d1 = params["demand_task1"]               # required effective hours, task 1
    d2 = params["demand_task2"]               # required effective hours, task 2
    d3 = params["demand_task3"]               # required effective hours, task 3
    max_s = params["max_skilled"]
    max_l = params["max_laborers"]

    # ---- Decision variables (integer numbers of workers/groups) ----
    # Task 1: s1 = skilled working alone, g1 = groups (1 skilled + 2 laborers)
    # Task 2: x2 = skilled workers, y2 = laborers (each works individually)
    # Task 3: x3 = groups (1 skilled + 3 laborers), p3 = pure laborer groups (5 laborers)
    model = gp.Model("workforce_hiring")
    model.Params.OutputFlag = 0

    s1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="solo_skilled_task1")
    g1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="groups_task1")
    x2 = model.addVar(vtype=GRB.INTEGER, lb=0, name="skilled_task2")
    y2 = model.addVar(vtype=GRB.INTEGER, lb=0, name="laborers_task2")
    x3 = model.addVar(vtype=GRB.INTEGER, lb=0, name="led_groups_task3")
    p3 = model.addVar(vtype=GRB.INTEGER, lb=0, name="pure_groups_task3")

    # ---- Task hour requirements (group outputs use the effective hours) ----
    # Task 1: solo skilled gives h_s hours; a 1+2 group gives h_s + 2*h_l
    model.addConstr(h_s * s1 + (h_s + 2 * h_l) * g1 >= d1, "task1_hours")
    # Task 2: each skilled gives h_s, each laborer gives h_l
    model.addConstr(h_s * x2 + h_l * y2 >= d2, "task2_hours")
    # Task 3: led group gives h_s + 3*h_l; pure 5-laborer group gives 5*h_l
    model.addConstr((h_s + 3 * h_l) * x3 + 5 * h_l * p3 >= d3, "task3_hours")

    # ---- Recruitment limits ----
    # Skilled workers: solo + group leaders (task1), task2, task3 leaders
    model.addConstr(s1 + g1 + x2 + x3 <= max_s, "skilled_limit")
    # Laborers: 2 per task1 group, task2, 3 per task3 led group, 5 per pure group
    model.addConstr(2 * g1 + y2 + 3 * x3 + 5 * p3 <= max_l, "laborer_limit")

    # ---- Objective: minimize total weekly wages ----
    total_cost = (wage_s * (s1 + g1 + x2 + x3)
                  + wage_l * (2 * g1 + y2 + 3 * x3 + 5 * p3))
    model.setObjective(total_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no optimal solution"}