import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_pair = params["profit_per_pair"]
    fulltime_sales_rate = params["fulltime_sales_rate"]
    parttime_sales_rate = params["parttime_sales_rate"]
    fulltime_salary = params["fulltime_salary"]
    parttime_salary = params["parttime_salary"]
    fulltime_overtime_pay = params["fulltime_overtime_pay"]
    parttime_overtime_pay = params["parttime_overtime_pay"]
    fulltime_hours = params["fulltime_hours"]
    parttime_hours = params["parttime_hours"]
    sales_target = params["sales_target"]
    fulltime_overtime_limit = params["fulltime_overtime_limit"]

    # Number of full-time and part-time salespeople
    n_fulltime = 5
    n_parttime = 4

    model = gp.Model("shoe_store_goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: overtime hours for full-time (x1) and part-time (x2)
    x1 = model.addVar(lb=0.0, name="x1")  # overtime hours per full-time salesperson
    x2 = model.addVar(lb=0.0, name="x2")  # overtime hours per part-time salesperson

    # Goal deviation variables (non-negative)
    # p1: sales target - d1_minus (underachievement), d1_plus (overachievement)
    d1_minus = model.addVar(lb=0.0, name="d1_minus")
    d1_plus  = model.addVar(lb=0.0, name="d1_plus")

    # p2: fulltime overtime limit - d2_minus, d2_plus
    d2_minus = model.addVar(lb=0.0, name="d2_minus")
    d2_plus  = model.addVar(lb=0.0, name="d2_plus")

    # p3: full employment goals
    # Full-time: total hours = n_fulltime * fulltime_hours (target), deviation d3f
    d3f_minus = model.addVar(lb=0.0, name="d3f_minus")
    d3f_plus  = model.addVar(lb=0.0, name="d3f_plus")
    # Part-time: total hours = n_parttime * parttime_hours (target), deviation d3p
    d3p_minus = model.addVar(lb=0.0, name="d3p_minus")
    d3p_plus  = model.addVar(lb=0.0, name="d3p_plus")

    # p4: minimize overtime hours
    # d4f = overtime hours for full-time staff (total), d4p = part-time
    d4f = model.addVar(lb=0.0, name="d4f")
    d4p = model.addVar(lb=0.0, name="d4p")

    # Total sales volume
    # Full-time: each works fulltime_hours + x1 hours; n_fulltime people
    # Part-time: each works parttime_hours + x2 hours; n_parttime people
    total_sales = (n_fulltime * (fulltime_hours + x1) * fulltime_sales_rate +
                   n_parttime * (parttime_hours + x2) * parttime_sales_rate)

    # Goal constraints
    # p1: total sales >= sales_target
    model.addConstr(
        total_sales - d1_plus + d1_minus == sales_target,
        name="goal_sales"
    )

    # p2: full-time overtime <= fulltime_overtime_limit
    # x1 is per-person overtime; total full-time overtime = n_fulltime * x1
    # The constraint is on per-person overtime: x1 <= fulltime_overtime_limit
    model.addConstr(
        x1 - d2_plus + d2_minus == fulltime_overtime_limit,
        name="goal_ft_overtime"
    )

    # p3a: full-time total working hours = n_fulltime * fulltime_hours (fully employed = no overtime ideally)
    # "fully employed" means actual hours >= standard hours, so we track underemployment
    # Total full-time hours worked = n_fulltime * (fulltime_hours + x1)
    # Target = n_fulltime * fulltime_hours (standard hours)
    model.addConstr(
        n_fulltime * (fulltime_hours + x1) - d3f_plus + d3f_minus == n_fulltime * fulltime_hours,
        name="goal_ft_employment"
    )

    # p3b: part-time total working hours = n_parttime * parttime_hours
    model.addConstr(
        n_parttime * (parttime_hours + x2) - d3p_plus + d3p_minus == n_parttime * parttime_hours,
        name="goal_pt_employment"
    )

    # p4: overtime hours auxiliary constraints
    # d4f represents total full-time overtime = n_fulltime * x1
    model.addConstr(d4f == n_fulltime * x1, name="def_d4f")
    # d4p represents total part-time overtime = n_parttime * x2
    model.addConstr(d4p == n_parttime * x2, name="def_d4p")

    # Preemptive goal programming using weighted sum with large penalty weights
    # Priority levels: p1 >> p2 >> p3 >> p4
    # Weights chosen as powers of M (big-M approach for preemptive ordering)
    M = 1e6

    # p1: minimize underachievement of sales target (d1_minus)
    # p2: minimize overachievement of fulltime overtime (d2_plus)
    # p3: minimize underemployment, full-time weighted double (2*d3f_minus + d3p_minus)
    #     (fully employed means no under-hours; since overtime is positive, d3f_minus=0 always,
    #      but we also don't want over-staffing shortfall - interpret as: minimize deviations from standard)
    # p4: minimize total overtime (d4f + d4p)

    obj = (M**3 * d1_minus +
           M**2 * d2_plus +
           M**1 * (2.0 * d3f_minus + d3p_minus) +
           1.0  * (d4f + d4p))

    model.setObjective(obj, GRB.MINIMIZE)

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