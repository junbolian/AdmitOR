import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = ["Donghai", "Nanjiang"]
    specialties = [1, 2, 3]

    model.CITY = pyo.Set(initialize=cities, ordered=True)
    model.SPEC = pyo.Set(initialize=specialties, ordered=True)

    # demand
    demand = {
        ("Donghai", 1): params["demand_Donghai_1"],
        ("Donghai", 2): params["demand_Donghai_2"],
        ("Donghai", 3): params["demand_Donghai_3"],
        ("Nanjiang", 1): params["demand_Nanjiang_1"],
        ("Nanjiang", 2): params["demand_Nanjiang_2"],
        ("Nanjiang", 3): params["demand_Nanjiang_3"],
    }

    count = {
        1: params["count_type_1"],
        2: params["count_type_2"],
        3: params["count_type_3"],
        4: params["count_type_4"],
        5: params["count_type_5"],
        6: params["count_type_6"],
    }

    p2_target = params["p2_target"]
    p3_target = params["p3_target"]

    TYPES = [1, 2, 3, 4, 5, 6]
    model.T = pyo.Set(initialize=TYPES, ordered=True)

    # suitable specializations per type
    suitable = {
        1: [1, 2],
        2: [2, 3],
        3: [1, 3],
        4: [1, 3],
        5: [2, 3],
        6: [3],
    }
    preferred_spec = {1: 1, 2: 2, 3: 1, 4: 3, 5: 3, 6: 3}
    preferred_city = {
        1: "Donghai",
        2: "Donghai",
        3: "Nanjiang",
        4: "Nanjiang",
        5: "Donghai",
        6: "Nanjiang",
    }

    # arcs: (type, specialization, city) for suitable (spec, type)
    arcs = []
    for t in TYPES:
        for s in suitable[t]:
            for c in cities:
                arcs.append((t, s, c))

    model.A = pyo.Set(initialize=arcs, dimen=3)

    # base assignment variables
    model.x = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)

    # deficit (unmet demand) variables
    model.d = pyo.Var(model.CITY, model.SPEC, domain=pyo.NonNegativeIntegers)

    # priority slack variables
    model.s2 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.s3 = pyo.Var(domain=pyo.NonNegativeIntegers)

    # demand constraints
    def demand_rule(m, c, s):
        return sum(m.x[t, ss, cc] for (t, ss, cc) in m.A
                   if ss == s and cc == c) + m.d[c, s] >= demand[(c, s)]
    model.demand_con = pyo.Constraint(model.CITY, model.SPEC, rule=demand_rule)

    # availability constraints
    def avail_rule(m, t):
        return sum(m.x[t, s, c] for (tt, s, c) in m.A if tt == t) <= count[t]
    model.avail_con = pyo.Constraint(model.T, rule=avail_rule)

    # preferred specialty matches
    def pref_spec_expr(m):
        return sum(m.x[t, s, c] for (t, s, c) in m.A if s == preferred_spec[t])
    model.pref_spec_expr = pyo.Expression(rule=pref_spec_expr)

    # preferred city matches
    def pref_city_expr(m):
        return sum(m.x[t, s, c] for (t, s, c) in m.A if c == preferred_city[t])
    model.pref_city_expr = pyo.Expression(rule=pref_city_expr)

    # priority 2 constraint: pref spec matches + slack >= target
    model.p2_con = pyo.Constraint(
        expr=model.pref_spec_expr + model.s2 >= p2_target
    )

    # priority 3 constraint: pref city matches + slack >= target
    model.p3_con = pyo.Constraint(
        expr=model.pref_city_expr + model.s3 >= p3_target
    )

    # Objective: lexicographic approximation.
    # Large weights to enforce priority order: p1 (unmet) >> p2 (spec slack) >> p3 (city slack)
    # p1 is captured as total unmet demand (sum of d).
    big1 = 1e8
    big2 = 1e4

    def obj_rule(m):
        total_deficit = sum(m.d[c, s] for c in m.CITY for s in m.SPEC)
        return big1 * total_deficit + big2 * m.s2 + m.s3
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}