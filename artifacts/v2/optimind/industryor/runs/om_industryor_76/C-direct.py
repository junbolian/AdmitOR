import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_pair = params["profit_per_pair"]
    full_time_count = params["full_time_count"]
    part_time_count = params["part_time_count"]
    full_time_monthly_hours = params["full_time_monthly_hours"]
    part_time_monthly_hours = params["part_time_monthly_hours"]
    full_time_sales_rate = params["full_time_sales_rate"]
    part_time_sales_rate = params["part_time_sales_rate"]
    full_time_wage = params["full_time_wage"]
    part_time_wage = params["part_time_wage"]
    full_time_overtime_pay = params["full_time_overtime_pay"]
    part_time_overtime_pay = params["part_time_overtime_pay"]
    sales_target = params["sales_target"]

    # Regular sales capacity
    regular_sales = (full_time_sales_rate * full_time_monthly_hours * full_time_count
                     + part_time_sales_rate * part_time_monthly_hours * part_time_count)

    model = gp.Model("shoe_store_goal_programming")
    model.setParam("OutputFlag", 0)

    # Overtime hours (total, across all clerks of each type)
    x1 = model.addVar(lb=0.0, name="overtime_fulltime")   # total overtime hours for full-time clerks
    x2 = model.addVar(lb=0.0, name="overtime_parttime")   # total overtime hours for part-time clerks

    # Goal p1: achieve sales_target pairs
    # Total sales = regular_sales + full_time_sales_rate*x1 + part_time_sales_rate*x2
    # deviation: d1_minus = shortfall below target, d1_plus = excess above target
    d1_minus = model.addVar(lb=0.0, name="d1_minus")  # underachievement of p1
    d1_plus  = model.addVar(lb=0.0, name="d1_plus")   # overachievement of p1

    # Goal p2: full employment — clerks should not be under-utilized in regular hours.
    # Since we model only overtime on top of fixed regular hours, full employment
    # (all regular hours are worked) is structurally enforced. We model p2 as:
    # no forced idle time, i.e., d2_minus (underemployment deviation) = 0.
    # We capture this by ensuring total hours >= regular_hours (already guaranteed),
    # so d2_minus is pinned to 0. We still include it for completeness.
    d2_minus = model.addVar(lb=0.0, name="d2_minus")  # underemployment deviation
    d2_plus  = model.addVar(lb=0.0, name="d2_plus")   # overemployment (overtime) deviation

    # Goal p3: minimize total overtime hours
    d3_minus = model.addVar(lb=0.0, name="d3_minus")
    d3_plus  = model.addVar(lb=0.0, name="d3_plus")

    model.update()

    # Constraint for goal p1: sales deviation
    # regular_sales + rate_ft*x1 + rate_pt*x2 - d1_plus + d1_minus = sales_target
    model.addConstr(
        regular_sales + full_time_sales_rate * x1 + part_time_sales_rate * x2
        - d1_plus + d1_minus == sales_target,
        name="goal_p1"
    )

    # Constraint for goal p2: full employment deviation
    # Total regular hours = full_time_monthly_hours*full_time_count + part_time_monthly_hours*part_time_count
    total_regular_hours = (full_time_monthly_hours * full_time_count
                           + part_time_monthly_hours * part_time_count)
    # Total actual hours = total_regular_hours + x1 + x2
    # d2_plus represents overtime (excess over regular), d2_minus represents idle time
    model.addConstr(
        total_regular_hours + x1 + x2 - d2_plus + d2_minus == total_regular_hours,
        name="goal_p2"
    )
    # This simplifies to: x1 + x2 = d2_plus - d2_minus, so d2_plus = x1+x2, d2_minus=0

    # Constraint for goal p3: minimize overtime
    # overtime = x1 + x2; we want this minimized, so d3_plus = excess overtime
    model.addConstr(
        x1 + x2 - d3_plus + d3_minus == 0,
        name="goal_p3"
    )
    # d3_plus = x1+x2 (total overtime), d3_minus = 0

    # Preemptive goal programming via large penalty weights:
    # Priority 1 (p1): minimize d1_minus (sales shortfall) — weight M^2
    # Priority 2 (p2): minimize d2_minus (underemployment) — weight M
    # Priority 3 (p3): minimize d3_plus (total overtime) — weight 1
    # Using M = a large number relative to realistic values
    BIG_M = 1e6

    model.setObjective(
        BIG_M * BIG_M * d1_minus
        + BIG_M * d2_minus
        + d3_plus,
        GRB.MINIMIZE
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        # Compute objective as net profit: revenue from sales minus labor costs
        total_sales = regular_sales + full_time_sales_rate * x1.X + part_time_sales_rate * x2.X
        revenue = profit_per_pair * total_sales
        regular_labor_cost = (full_time_wage * full_time_monthly_hours * full_time_count
                              + part_time_wage * part_time_monthly_hours * part_time_count)
        overtime_labor_cost = (full_time_overtime_pay * x1.X
                               + part_time_overtime_pay * x2.X)
        net_profit = revenue - regular_labor_cost - overtime_labor_cost
        return {"objective": float(net_profit), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}