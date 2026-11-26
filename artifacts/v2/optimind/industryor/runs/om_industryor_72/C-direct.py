import gurobipy as gp
from gurobipy import GRB

def solve(params):
    durations = params["durations"]
    work_cost_per_day = params["work_cost_per_day"]
    machine_cost_per_day = params["machine_cost_per_day"]

    # Activity durations
    d_A = durations[0]
    d_B = durations[1]
    d_C = durations[2]
    d_D = durations[3]
    d_E = durations[4]
    d_F = durations[5]
    d_G = durations[6]

    model = gp.Model("project_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables: start times for each activity
    s_A = model.addVar(lb=0, name="s_A")
    s_B = model.addVar(lb=0, name="s_B")
    s_C = model.addVar(lb=0, name="s_C")
    s_D = model.addVar(lb=0, name="s_D")
    s_E = model.addVar(lb=0, name="s_E")
    s_F = model.addVar(lb=0, name="s_F")
    s_G = model.addVar(lb=0, name="s_G")

    # Project completion time (makespan)
    T = model.addVar(lb=0, name="T")

    model.update()

    # Precedence constraints: A -> G, D
    model.addConstr(s_G >= s_A + d_A, name="A_before_G")
    model.addConstr(s_D >= s_A + d_A, name="A_before_D")

    # E, G -> F
    model.addConstr(s_F >= s_E + d_E, name="E_before_F")
    model.addConstr(s_F >= s_G + d_G, name="G_before_F")

    # D, F -> C
    model.addConstr(s_C >= s_D + d_D, name="D_before_C")
    model.addConstr(s_C >= s_F + d_F, name="F_before_C")

    # F -> B
    model.addConstr(s_B >= s_F + d_F, name="F_before_B")

    # T >= finish time of every activity
    model.addConstr(T >= s_A + d_A, name="T_A")
    model.addConstr(T >= s_B + d_B, name="T_B")
    model.addConstr(T >= s_C + d_C, name="T_C")
    model.addConstr(T >= s_D + d_D, name="T_D")
    model.addConstr(T >= s_E + d_E, name="T_E")
    model.addConstr(T >= s_F + d_F, name="T_F")
    model.addConstr(T >= s_G + d_G, name="T_G")

    # Machine rental duration: from start of A to end of B
    # end_B = s_B + d_B, machine_duration = s_B + d_B - s_A
    machine_duration = model.addVar(lb=0, name="machine_duration")
    model.addConstr(machine_duration == s_B + d_B - s_A, name="machine_duration_def")

    # Objective: minimize total cost
    # Work cost = work_cost_per_day * T
    # Machine cost = machine_cost_per_day * machine_duration
    model.setObjective(
        work_cost_per_day * T + machine_cost_per_day * machine_duration,
        GRB.MINIMIZE
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