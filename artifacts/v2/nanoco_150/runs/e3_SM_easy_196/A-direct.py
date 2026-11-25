import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    architect_rankings = params["architect_rankings"]
    engineer_rankings = params["engineer_rankings"]
    w_arch = params["friction_cost_architect_rank_weight"]
    w_eng = params["friction_cost_engineer_rank_weight"]

    n = len(architect_rankings)
    architects = list(range(n))
    engineers = list(range(n))

    # Position of engineer e in architect a's ranking
    arch_pos = {}
    for a in architects:
        for pos, e in enumerate(architect_rankings[a]):
            arch_pos[(a, e)] = pos

    # Position of architect a in engineer e's ranking
    eng_pos = {}
    for e in engineers:
        for pos, a in enumerate(engineer_rankings[e]):
            eng_pos[(e, a)] = pos

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=architects)
    model.E = pyo.Set(initialize=engineers)
    model.Pairs = pyo.Set(
        initialize=[(a, e) for a in architects for e in engineers], dimen=2
    )

    model.x = pyo.Var(model.Pairs, domain=pyo.Binary)

    def arch_match_rule(mdl, a):
        return sum(mdl.x[a, e] for e in engineers) == 1

    model.arch_match = pyo.Constraint(model.A, rule=arch_match_rule)

    def eng_match_rule(mdl, e):
        return sum(mdl.x[a, e] for a in architects) == 1

    model.eng_match = pyo.Constraint(model.E, rule=eng_match_rule)

    # Stability: no blocking pair.
    # For each (a, e): a strictly prefers e over any partner ranked worse than e,
    # and e strictly prefers a over any partner ranked worse than a.
    # Use strict preference to avoid degenerate blocking on equal ranks (impossible
    # here since rankings are strict, but the (a,e) cell itself must be excluded).
    def stability_rule(mdl, a, e):
        # e' that architect a strictly prefers to e (lower position)
        arch_pref = [ep for ep in engineers if arch_pos[(a, ep)] < arch_pos[(a, e)]]
        # a' that engineer e strictly prefers to a (lower position)
        eng_pref = [ap for ap in architects if eng_pos[(e, ap)] < eng_pos[(e, a)]]
        lhs = sum(mdl.x[a, ep] for ep in arch_pref) + sum(mdl.x[ap, e] for ap in eng_pref)
        return lhs <= 1

    model.stability = pyo.Constraint(model.Pairs, rule=stability_rule)

    def obj_rule(mdl):
        return sum(
            (w_arch * arch_pos[(a, e)] + w_eng * eng_pos[(e, a)]) * mdl.x[a, e]
            for a in architects
            for e in engineers
        )

    model.total_friction = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_friction))
    return {"objective": obj_val, "status": "optimal"}