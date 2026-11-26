import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["donghai", "nanjiang"]
    majors = [1, 2, 3]

    # Category -> (competent majors, preferred major, preferred city)
    competent = {
        1: [1, 2],
        2: [2, 3],
        3: [1, 3],
        4: [1, 3],
        5: [2, 3],
        6: [3],
    }
    pref_major = {1: 1, 2: 2, 3: 1, 4: 3, 5: 3, 6: 3}
    pref_city = {
        1: "donghai",
        2: "donghai",
        3: "nanjiang",
        4: "nanjiang",
        5: "donghai",
        6: "nanjiang",
    }

    cats = list(range(1, 7))

    size = {
        1: params["category1_size"],
        2: params["category2_size"],
        3: params["category3_size"],
        4: params["category4_size"],
        5: params["category5_size"],
        6: params["category6_size"],
    }

    demand = {}
    for c in cities:
        for j in majors:
            demand[(c, j)] = params[f"demand_{c}_major{j}"]

    p2_goal = params["preferred_major_goal"]
    p3_goal = params["preferred_city_goal"]

    model = pyo.ConcreteModel()

    # x[(k, c, j)] : personnel from category k assigned to city c in major j
    allowed = [(k, c, j) for k in cats for c in cities for j in majors if j in competent[k]]
    model.x = pyo.Var(allowed, domain=pyo.NonNegativeIntegers)

    # Totals per category capped by size
    model.cat_cap = pyo.Constraint(
        cats,
        rule=lambda mdl, k: sum(mdl.x[k, c, j] for (kk, c, j) in allowed if kk == k) <= size[k],
    )

    # p1: demands met exactly (all three personnel types satisfied)
    model.demand_con = pyo.Constraint(
        [(c, j) for c in cities for j in majors],
        rule=lambda mdl, c, j: sum(mdl.x[k, cc, jj] for (k, cc, jj) in allowed if cc == c and jj == j)
        == demand[(c, j)],
    )

    # Personnel satisfying preferred major
    model.pref_major_count = pyo.Expression(
        expr=sum(
            model.x[k, c, j]
            for (k, c, j) in allowed
            if j == pref_major[k]
        )
    )

    # Personnel satisfying preferred city
    model.pref_city_count = pyo.Expression(
        expr=sum(
            model.x[k, c, j]
            for (k, c, j) in allowed
            if c == pref_city[k]
        )
    )

    # Deviations for goals p2 and p3 (only undershoot penalized via priority weights)
    model.d2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3 = pyo.Var(domain=pyo.NonNegativeReals)

    model.p2_con = pyo.Constraint(expr=model.pref_major_count + model.d2 >= p2_goal)
    model.p3_con = pyo.Constraint(expr=model.pref_city_count + model.d3 >= p3_goal)

    # Lexicographic priorities represented by large weights
    # p1 handled as hard constraint; p2 >> p3
    model.obj = pyo.Objective(
        expr=1e6 * model.d2 + 1.0 * model.d3,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}