import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    men_pref = params["men_preferences"]
    women_pref = params["women_preferences"]
    num_men = params["num_men"]
    num_women = params["num_women"]

    men = list(range(num_men))
    women = list(range(num_women))

    man_rank = {i: {j: r for r, j in enumerate(men_pref[i])} for i in men}
    woman_rank = {j: {i: r for r, i in enumerate(women_pref[j])} for j in women}

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=men)
    model.W = pyo.Set(initialize=women)

    model.match = pyo.Var(model.M, model.W, domain=pyo.Binary)

    def man_rule(mdl, i):
        return sum(mdl.match[i, j] for j in mdl.W) == 1

    model.man_constraint = pyo.Constraint(model.M, rule=man_rule)

    def woman_rule(mdl, j):
        return sum(mdl.match[i, j] for i in mdl.M) == 1

    model.woman_constraint = pyo.Constraint(model.W, rule=woman_rule)

    BIGM = num_men + num_women

    model.unmatched = pyo.Var(model.M, model.W, domain=pyo.Binary)
    model.man_pref_aux = pyo.Var(model.M, model.W, domain=pyo.Binary)
    model.woman_pref_aux = pyo.Var(model.M, model.W, domain=pyo.Binary)

    def man_partner_rank(mdl, i):
        return sum(man_rank[i][k] * mdl.match[i, k] for k in mdl.W)

    def woman_partner_rank(mdl, j):
        return sum(woman_rank[j][h] * mdl.match[h, j] for h in mdl.M)

    def unmatched_rule(mdl, i, j):
        return mdl.unmatched[i, j] == 1 - mdl.match[i, j]

    model.unmatched_constraint = pyo.Constraint(model.M, model.W, rule=unmatched_rule)

    def man_pref_rule(mdl, i, j):
        return man_rank[i][j] >= man_partner_rank(mdl, i) + 1 - BIGM * (1 - mdl.man_pref_aux[i, j])

    model.man_pref_constraint = pyo.Constraint(model.M, model.W, rule=man_pref_rule)

    def man_pref_rule2(mdl, i, j):
        return man_rank[i][j] <= man_partner_rank(mdl, i) + BIGM * mdl.man_pref_aux[i, j]

    model.man_pref_constraint2 = pyo.Constraint(model.M, model.W, rule=man_pref_rule2)

    def woman_pref_rule(mdl, i, j):
        return woman_rank[j][i] >= woman_partner_rank(mdl, j) + 1 - BIGM * (1 - mdl.woman_pref_aux[i, j])

    model.woman_pref_constraint = pyo.Constraint(model.M, model.W, rule=woman_pref_rule)

    def woman_pref_rule2(mdl, i, j):
        return woman_rank[j][i] <= woman_partner_rank(mdl, j) + BIGM * mdl.woman_pref_aux[i, j]

    model.woman_pref_constraint2 = pyo.Constraint(model.M, model.W, rule=woman_pref_rule2)

    def no_block_rule(mdl, i, j):
        return mdl.unmatched[i, j] + mdl.man_pref_aux[i, j] + mdl.woman_pref_aux[i, j] <= 2

    model.no_block_constraint = pyo.Constraint(model.M, model.W, rule=no_block_rule)

    def obj_rule(mdl):
        return sum(
            (man_rank[i][j] + woman_rank[j][i]) * mdl.match[i, j]
            for i in mdl.M
            for j in mdl.W
        )

    model.egalitarian = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.egalitarian))
    return {"objective": obj_val, "status": "optimal"}