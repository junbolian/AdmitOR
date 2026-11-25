import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 7
    sp = params["supplier_pref_positions"]
    pp = params["plant_pref_positions"]

    model = pyo.ConcreteModel()
    model.S = pyo.RangeSet(0, n - 1)
    model.P = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.S, model.P, domain=pyo.Binary)

    def match_supplier_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.P) == 1

    def match_plant_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.S) == 1

    model.supplier_match = pyo.Constraint(model.S, rule=match_supplier_rule)
    model.plant_match = pyo.Constraint(model.P, rule=match_plant_rule)

    # Blocking pair (i on supplier side, j on plant side):
    # supplier i prefers j over its partner  <=>  sp[i][j] < sp[i][partner_of_i]
    # plant j prefers i over its partner     <=>  pp[j][i] < pp[j][partner_of_j]
    # Introduce linearization via indicator: forbid x[i,j]=0 while both hold.
    # Equivalent: for each (i,j), x[i,j] >= 1 - [supplier wants better] - [plant wants better]
    # Using binary helper is cleaner. We express with constraints on partner positions:
    # If x[i,j] = 0 and supplier i prefers j strictly, then plant j must NOT prefer i over its partner.
    #
    # Linearize using big-M style auxiliary binaries:
    model.y = pyo.Var(model.S, model.P, domain=pyo.Binary)  # y[i,j]=1 if supplier i strictly prefers j over partner

    M = n

    def supplier_prefers_rule(mdl, i, j):
        # sum_k sp[i][k]*x[i,k] is partner position of i. If sp[i][j] < that -> y=1
        partner_pos = sum(sp[i][k] * mdl.x[i, k] for k in mdl.P)
        return partner_pos - sp[i][j] <= M * (1 - mdl.y[i, j])

    def supplier_not_prefers_rule(mdl, i, j):
        partner_pos = sum(sp[i][k] * mdl.x[i, k] for k in mdl.P)
        return partner_pos - sp[i][j] >= 1 - M * mdl.y[i, j]

    model.supp_prefer = pyo.Constraint(model.S, model.P, rule=supplier_prefers_rule)
    model.supp_not_prefer = pyo.Constraint(model.S, model.P, rule=supplier_not_prefers_rule)

    model.z = pyo.Var(model.S, model.P, domain=pyo.Binary)  # z[i,j]=1 if plant j strictly prefers i over partner

    def plant_prefers_rule(mdl, i, j):
        partner_pos = sum(pp[j][k] * mdl.x[k, j] for k in mdl.S)
        return partner_pos - pp[j][i] <= M * (1 - mdl.z[i, j])

    def plant_not_prefers_rule(mdl, i, j):
        partner_pos = sum(pp[j][k] * mdl.x[k, j] for k in mdl.S)
        return partner_pos - pp[j][i] >= 1 - M * mdl.z[i, j]

    model.plant_prefer = pyo.Constraint(model.S, model.P, rule=plant_prefers_rule)
    model.plant_not_prefer = pyo.Constraint(model.S, model.P, rule=plant_not_prefers_rule)

    # Stability: cannot have x[i,j]=0 with y[i,j]=1 and z[i,j]=1
    def stability_rule(mdl, i, j):
        return mdl.x[i, j] + mdl.y[i, j] + mdl.z[i, j] <= 2

    model.stability = pyo.Constraint(model.S, model.P, rule=stability_rule)

    def risk_rule(mdl):
        return sum(
            (sp[i][j] + pp[j][i]) * mdl.x[i, j]
            for i in mdl.S
            for j in mdl.P
        )

    model.risk = pyo.Objective(rule=risk_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.risk))
    return {"objective": obj_val, "status": "optimal"}