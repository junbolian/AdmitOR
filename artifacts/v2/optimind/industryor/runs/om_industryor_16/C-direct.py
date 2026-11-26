import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_rate = params["production_rate"]   # meters per hour
    regular_time    = params["regular_time"]       # 110 hours
    overtime_limit  = params["overtime_limit"]     # 10 hours
    curtain_demand  = params["curtain_demand"]     # 70000 meters
    curtain_profit  = params["curtain_profit"]     # 2.5 yuan/meter
    clothing_demand = params["clothing_demand"]    # 45000 meters
    clothing_profit = params["clothing_profit"]    # 1.5 yuan/meter

    # ------------------------------------------------------------------ #
    # Decision variables
    #   x1  = hours producing curtain fabric
    #   x2  = hours producing clothing fabric
    #
    # Goal-programming deviation variables (all >= 0):
    #   d1m / d1p  : under / over for p1 (full utilisation of regular_time)
    #   d2p        : over  for p2 (overtime exceeds overtime_limit)
    #   d3am/ d3ap : under / over for p3-curtain  demand
    #   d3bm/ d3bp : under / over for p3-clothing demand
    #   d4p        : overtime itself (= d1p)  — reuse d1p for p4
    # ------------------------------------------------------------------ #

    model = gp.Model("textile_goal_programming")
    model.setParam("OutputFlag", 0)

    # Production hours
    x1 = model.addVar(lb=0.0, name="x1_curtain_hours")
    x2 = model.addVar(lb=0.0, name="x2_clothing_hours")

    # Deviation variables
    d1m = model.addVar(lb=0.0, name="d1m")   # underutilisation of regular time
    d1p = model.addVar(lb=0.0, name="d1p")   # overtime (= total time - regular_time)
    d2p = model.addVar(lb=0.0, name="d2p")   # overtime beyond overtime_limit
    d3am = model.addVar(lb=0.0, name="d3am") # curtain shortfall vs demand
    d3ap = model.addVar(lb=0.0, name="d3ap") # curtain surplus  vs demand
    d3bm = model.addVar(lb=0.0, name="d3bm") # clothing shortfall vs demand
    d3bp = model.addVar(lb=0.0, name="d3bp") # clothing surplus  vs demand

    # ------------------------------------------------------------------ #
    # Goal constraints
    # ------------------------------------------------------------------ #

    # G1: total production time = regular_time + overtime
    #     x1 + x2 - d1p + d1m = regular_time
    model.addConstr(x1 + x2 - d1p + d1m == regular_time, name="g1_utilisation")

    # G2: overtime (d1p) should not exceed overtime_limit
    #     d1p - d2p + d2m = overtime_limit  →  we only penalise d2p (excess beyond limit)
    #     d2p = max(0, d1p - overtime_limit)
    model.addConstr(d1p - d2p <= overtime_limit, name="g2_overtime_limit")

    # G3a: curtain production meets curtain_demand
    #      production_rate * x1 - d3ap + d3am = curtain_demand
    model.addConstr(production_rate * x1 - d3ap + d3am == curtain_demand, name="g3a_curtain")

    # G3b: clothing production meets clothing_demand
    #      production_rate * x2 - d3bp + d3bm = clothing_demand
    model.addConstr(production_rate * x2 - d3bp + d3bm == clothing_demand, name="g3b_clothing")

    # ------------------------------------------------------------------ #
    # Preemptive (lexicographic) goal programming via weighted penalty.
    # Weights reflect strict priority ordering p1 >> p2 >> p3 >> p4.
    # We use large penalty multipliers: p1=M^3, p2=M^2, p3=M, p4=1
    # with M chosen large enough that lower-priority terms cannot
    # compensate a unit of higher-priority deviation.
    #
    # Maximum possible deviation for each goal (bounds the needed M):
    #   p1: d1m or d1p <= regular_time + max_overtime ~ 120
    #   p2: d2p <= overtime_limit                     ~ 10
    #   p3: d3am <= curtain_demand                    ~ 70000
    #        d3bm <= clothing_demand                  ~ 45000
    #   p4: d1p  <= regular_time + overtime_limit     ~ 120
    #
    # M = 1e6 safely dominates all cross-priority terms.
    # ------------------------------------------------------------------ #
    M = 1e6

    obj = (
        M**3 * d1m          # p1: minimise underutilisation (must fully use regular time)
      + M**2 * d2p          # p2: minimise overtime beyond overtime_limit
      + M    * (d3am + d3bm)# p3: minimise shortfall in curtain and clothing sales
      + 1.0  * d1p          # p4: minimise overtime (d1p is the overtime variable)
    )

    model.setObjective(obj, GRB.MINIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or status == GRB.SUBOPTIMAL:
        # Compute actual profit from production plan
        curtain_meters  = production_rate * x1.X
        clothing_meters = production_rate * x2.X
        profit = curtain_profit * curtain_meters + clothing_profit * clothing_meters

        return {"objective": profit, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}