import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Months Jul..Dec indices 0..5 correspond to calendar months 7..12 (1-based)
    months = list(range(6))

    demand_I = params["demand_I"]   # Jan..Dec
    demand_II = params["demand_II"]  # Jan..Dec

    pc_I = params["prod_cost_I"]
    pc_I_late = params["prod_cost_I_late"]
    pc_II = params["prod_cost_II"]
    pc_II_late = params["prod_cost_II_late"]

    cap = params["cap_month"]
    vol_I = params["vol_I"]
    vol_II = params["vol_II"]
    wh_cap = params["wh_cap"]
    hold_own = params["hold_own"]
    hold_rent = params["hold_rent"]

    # July..Dec map to calendar index 6..11 (0-based)
    late_cut = 5  # months 0..5 in this horizon: Jul is calendar month 7 (index 6)
    # Production cost per product per horizon month (Jun-Dec pricing applies for Jul-Dec)
    def cost_I(t):
        # calendar month = t + 7
        return pc_I if (t + 7) <= 5 else pc_I_late

    def cost_II(t):
        return pc_II if (t + 7) <= 5 else pc_II_late

    def dem_I(t):
        return demand_I[t + 6]

    def dem_II(t):
        return demand_II[t + 6]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=months, ordered=True)

    model.xI = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.xII = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.invI = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.invII = pyo.Var(model.T, within=pyo.NonNegativeReals)
    # own-warehouse volume usage per month
    model.ownVol = pyo.Var(model.T, within=pyo.NonNegativeReals)
    # rented-warehouse volume usage per month
    model.rentVol = pyo.Var(model.T, within=pyo.NonNegativeReals)

    # Capacity constraint on combined production
    def cap_rule(m, t):
        return m.xI[t] + m.xII[t] <= cap
    model.cap_con = pyo.Constraint(model.T, rule=cap_rule)

    # Inventory balance: initial inventory at start of July = 0
    def invI_rule(m, t):
        prev = 0 if t == 0 else m.invI[t - 1]
        return m.invI[t] == prev + m.xI[t] - dem_I(t)
    model.invI_con = pyo.Constraint(model.T, rule=invI_rule)

    def invII_rule(m, t):
        prev = 0 if t == 0 else m.invII[t - 1]
        return m.invII[t] == prev + m.xII[t] - dem_II(t)
    model.invII_con = pyo.Constraint(model.T, rule=invII_rule)

    # Holding volume split into own + rented
    def vol_rule(m, t):
        return m.ownVol[t] + m.rentVol[t] == vol_I * m.invI[t] + vol_II * m.invII[t]
    model.vol_con = pyo.Constraint(model.T, rule=vol_rule)

    # Own warehouse capacity
    def own_cap_rule(m, t):
        return m.ownVol[t] <= wh_cap
    model.own_cap_con = pyo.Constraint(model.T, rule=own_cap_rule)

    # Objective: production + holding (own cheaper, rented more expensive)
    def obj_rule(m):
        prod = sum(
            cost_I(t) * m.xI[t] + cost_II(t) * m.xII[t]
            for t in m.T
        )
        hold = sum(
            hold_own * m.ownVol[t] + hold_rent * m.rentVol[t]
            for t in m.T
        )
        return prod + hold
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}