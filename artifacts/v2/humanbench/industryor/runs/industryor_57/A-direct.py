import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    area = params["area_per_store"]
    min_s = params["min_stores"]
    max_s = params["max_stores"]
    p1 = params["profit_type1"]
    p2 = params["profit_type2"]
    p3 = params["profit_type3"]
    p4 = params["profit_type4"]
    p5 = params["profit_type5"]
    rent = params["rent_share"]

    # per-store profit tables indexed by type (1..5), then position (0,1,2 for 1st..3rd store)
    profit = {1: p1, 2: p2, 3: p3, 4: p4, 5: p5}
    max_count = {1: 3, 2: 2, 3: 3, 4: 2, 5: 3}

    model = pyo.ConcreteModel()

    model.TYPES = pyo.Set(initialize=[1, 2, 3, 4, 5])
    model.UNITS = pyo.Set(initialize=[1, 2, 3])

    # y[t, k] = 1 if type t has at least k stores (k-th store opened)
    model.y = pyo.Var(model.TYPES, model.UNITS, domain=pyo.Binary)

    # enforce y[t,k] = 0 when k exceeds max_count for type t
    def _cap_rule(md, t, k):
        if k > max_count[t]:
            return md.y[t, k] == 0
        return pyo.Constraint.Skip

    model.cap_con = pyo.Constraint(model.TYPES, model.UNITS, rule=_cap_rule)

    # monotone nesting: y[t,k] <= y[t,k-1]
    def _nest_rule(md, t, k):
        if k >= 2 and k <= max_count[t]:
            return md.y[t, k] <= md.y[t, k - 1]
        return pyo.Constraint.Skip

    model.nest_con = pyo.Constraint(model.TYPES, model.UNITS, rule=_nest_rule)

    # number of stores per type
    def _num_rule(md, t):
        return sum(md.y[t, k] for k in md.UNITS if k <= max_count[t])

    model.num = pyo.Expression(model.TYPES, rule=_num_rule)

    # area constraint
    def _area_rule(md):
        return sum(area[t - 1] * md.num[t] for t in md.TYPES) <= 5000

    model.area_con = pyo.Constraint(rule=_area_rule)

    # min/max number constraints
    def _min_rule(md, t):
        return md.num[t] >= min_s[t - 1]

    model.min_con = pyo.Constraint(model.TYPES, rule=_min_rule)

    def _max_rule(md, t):
        if t <= len(max_s):
            return md.num[t] <= max_s[t - 1]
        return pyo.Constraint.Skip

    model.max_con = pyo.Constraint(model.TYPES, rule=_max_rule)

    # objective: rental income = rent_share * total profit
    # profit for type t with num stores = sum_k profit[t][k-1] * y[t,k]
    def _obj_rule(md):
        return rent * sum(
            profit[t][k - 1] * md.y[t, k]
            for t in md.TYPES
            for k in md.UNITS
            if k <= max_count[t]
        )

    model.obj = pyo.Objective(rule=_obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}