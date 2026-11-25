import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lab_preferences = params["lab_preferences"]
    site_preferences = params["site_preferences"]
    num_labs = params["num_labs"]
    num_sites = params["num_sites"]

    labs = list(range(num_labs))
    sites = list(range(num_sites))

    lab_rank = {}
    for i in labs:
        for pos, j in enumerate(lab_preferences[i]):
            lab_rank[(i, j)] = pos
    site_rank = {}
    for j in sites:
        for pos, i in enumerate(site_preferences[j]):
            site_rank[(i, j)] = pos

    model = pyo.ConcreteModel()
    model.Labs = pyo.Set(initialize=labs)
    model.Sites = pyo.Set(initialize=sites)

    model.x = pyo.Var(model.Labs, model.Sites, domain=pyo.Binary)

    def cost_rule(m):
        return sum(
            (lab_rank[(i, j)] + site_rank[(i, j)]) * m.x[i, j]
            for i in m.Labs
            for j in m.Sites
        )
    model.cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def lab_one_rule(m, i):
        return sum(m.x[i, j] for j in m.Sites) == 1
    model.lab_one = pyo.Constraint(model.Labs, rule=lab_one_rule)

    def site_one_rule(m, j):
        return sum(m.x[i, j] for i in m.Labs) == 1
    model.site_one = pyo.Constraint(model.Sites, rule=site_one_rule)

    model.a = pyo.Var(model.Labs, model.Sites, domain=pyo.Binary)
    model.b = pyo.Var(model.Labs, model.Sites, domain=pyo.Binary)

    def a_rule(m, i, j):
        preferred = [l for l in sites if lab_rank[(i, l)] < lab_rank[(i, j)]]
        return m.a[i, j] == sum(m.x[i, l] for l in preferred)
    model.a_con = pyo.Constraint(model.Labs, model.Sites, rule=a_rule)

    def b_rule(m, i, j):
        preferred = [k for k in labs if site_rank[(k, j)] < site_rank[(i, j)]]
        return m.b[i, j] == sum(m.x[k, j] for k in preferred)
    model.b_con = pyo.Constraint(model.Labs, model.Sites, rule=b_rule)

    def no_block_rule(m, i, j):
        return m.x[i, j] + m.a[i, j] + m.b[i, j] <= 2
    model.no_block = pyo.Constraint(model.Labs, model.Sites, rule=no_block_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}