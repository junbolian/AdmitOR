# IR: {"sets":{"I":"range(params['num_men'])","J":"range(params['num_women'])"},"params":{"num_men":"params['num_men']","num_women":"params['num_women']","men_preferences":"params['men_preferences']","women_preferences":"params['women_preferences']","men_rank[i,j]":"zero-based position of j in men_preferences[i]","women_rank[j,i]":"zero-based position of i in women_preferences[j]"},"variables":{"x[i,j]":"Binary; 1 iff man i is matched to woman j"},"constraints":["For each i: sum(j in J, x[i,j]) = 1","For each j: sum(i in I, x[i,j]) = 1","For each (i,j): x[i,j] + sum(k in J with men_rank[i,k] < men_rank[i,j], x[i,k]) + sum(h in I with women_rank[j,h] < women_rank[j,i], x[h,j]) >= 1"],"objective":"Minimize sum(i in I, j in J, (men_rank[i,j] + women_rank[j,i]) * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_men = params["num_men"]
    num_women = params["num_women"]
    men_preferences = params["men_preferences"]
    women_preferences = params["women_preferences"]

    if num_men <= 0 or num_women <= 0:
        return {"objective": None, "status": "invalid_dimensions"}

    if num_men != num_women:
        return {"objective": None, "status": "infeasible"}

    men = range(num_men)
    women = range(num_women)

    if len(men_preferences) != num_men or len(women_preferences) != num_women:
        return {"objective": None, "status": "invalid_preferences"}

    expected_men = set(men)
    expected_women = set(women)

    for man in men:
        preferences = men_preferences[man]
        if len(preferences) != num_women or set(preferences) != expected_women:
            return {"objective": None, "status": "invalid_preferences"}

    for woman in women:
        preferences = women_preferences[woman]
        if len(preferences) != num_men or set(preferences) != expected_men:
            return {"objective": None, "status": "invalid_preferences"}

    men_rank = {
        (man, woman): rank
        for man in men
        for rank, woman in enumerate(men_preferences[man])
    }
    women_rank = {
        (woman, man): rank
        for woman in women
        for rank, man in enumerate(women_preferences[woman])
    }

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=men, ordered=True)
    model.J = pyo.Set(initialize=women, ordered=True)

    model.men_rank = pyo.Param(
        model.I,
        model.J,
        initialize=men_rank,
        within=pyo.NonNegativeIntegers,
    )
    model.women_rank = pyo.Param(
        model.J,
        model.I,
        initialize=women_rank,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def man_assignment_rule(mdl, man):
        return sum(mdl.x[man, woman] for woman in mdl.J) == 1

    model.man_assignment = pyo.Constraint(
        model.I, rule=man_assignment_rule
    )

    def woman_assignment_rule(mdl, woman):
        return sum(mdl.x[man, woman] for man in mdl.I) == 1

    model.woman_assignment = pyo.Constraint(
        model.J, rule=woman_assignment_rule
    )

    def stability_rule(mdl, man, woman):
        return (
            mdl.x[man, woman]
            + sum(
                mdl.x[man, other_woman]
                for other_woman in mdl.J
                if men_rank[man, other_woman] < men_rank[man, woman]
            )
            + sum(
                mdl.x[other_man, woman]
                for other_man in mdl.I
                if women_rank[woman, other_man] < women_rank[woman, man]
            )
            >= 1
        )

    model.stability = pyo.Constraint(
        model.I, model.J, rule=stability_rule
    )

    model.egalitarian_score = pyo.Objective(
        expr=sum(
            (
                model.men_rank[man, woman]
                + model.women_rank[woman, man]
            )
            * model.x[man, woman]
            for man in model.I
            for woman in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.egalitarian_score))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}