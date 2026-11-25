# IR: {"sets":{"L":"range(num_labs)","S":"range(num_sites)","R":"range(rank_index_min,rank_index_max+1)"},"params":{"lab_preferences":"ordered site permutations indexed by L","site_preferences":"ordered lab permutations indexed by S","rank_index_min":"minimum rank","rank_index_max":"maximum rank","num_labs":"lab count","num_sites":"site count","lab_rank[l,s]":"rank_index_min + position of s in lab_preferences[l]","site_rank[s,l]":"rank_index_min + position of l in site_preferences[s]"},"variables":{"x[l,s]":"binary; 1 iff lab l is matched to site s"},"constraints":["For each l: sum_s x[l,s] = 1","For each s: sum_l x[l,s] = 1","For each (l,s): x[l,s] + sum_{t:lab_rank[l,t]<lab_rank[l,s]} x[l,t] + sum_{k:site_rank[s,k]<site_rank[s,l]} x[k,s] >= 1"],"objective":"minimize sum_{l,s} (lab_rank[l,s]+site_rank[s,l])*x[l,s]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lab_preferences = params["lab_preferences"]
    site_preferences = params["site_preferences"]
    rank_index_min = params["rank_index_min"]
    rank_index_max = params["rank_index_max"]
    num_labs = params["num_labs"]
    num_sites = params["num_sites"]

    labs = range(num_labs)
    sites = range(num_sites)
    ranks = range(rank_index_min, rank_index_max + 1)

    if (
        num_labs != num_sites
        or len(ranks) != num_labs
        or len(lab_preferences) != num_labs
        or len(site_preferences) != num_sites
    ):
        return {"objective": None, "status": "invalid_parameters"}

    expected_sites = set(sites)
    expected_labs = set(labs)

    if any(
        len(lab_preferences[lab]) != num_sites
        or set(lab_preferences[lab]) != expected_sites
        for lab in labs
    ):
        return {"objective": None, "status": "invalid_lab_preferences"}

    if any(
        len(site_preferences[site]) != num_labs
        or set(site_preferences[site]) != expected_labs
        for site in sites
    ):
        return {"objective": None, "status": "invalid_site_preferences"}

    lab_rank = {
        (lab, lab_preferences[lab][rank - rank_index_min]): rank
        for lab in labs
        for rank in ranks
    }
    site_rank = {
        (site, site_preferences[site][rank - rank_index_min]): rank
        for site in sites
        for rank in ranks
    }

    model = pyo.ConcreteModel()
    model.L = pyo.Set(initialize=labs, ordered=True)
    model.S = pyo.Set(initialize=sites, ordered=True)
    model.R = pyo.Set(initialize=ranks, ordered=True)

    model.lab_rank = pyo.Param(
        model.L, model.S, initialize=lab_rank, within=pyo.Integers
    )
    model.site_rank = pyo.Param(
        model.S, model.L, initialize=site_rank, within=pyo.Integers
    )
    model.x = pyo.Var(model.L, model.S, domain=pyo.Binary)

    def lab_assignment_rule(problem, lab):
        return sum(problem.x[lab, site] for site in problem.S) == 1

    model.lab_assignment = pyo.Constraint(
        model.L, rule=lab_assignment_rule
    )

    def site_assignment_rule(problem, site):
        return sum(problem.x[lab, site] for lab in problem.L) == 1

    model.site_assignment = pyo.Constraint(
        model.S, rule=site_assignment_rule
    )

    def stability_rule(problem, lab, site):
        preferred_sites = sum(
            problem.x[lab, other_site]
            for other_site in problem.S
            if lab_rank[lab, other_site] < lab_rank[lab, site]
        )
        preferred_labs = sum(
            problem.x[other_lab, site]
            for other_lab in problem.L
            if site_rank[site, other_lab] < site_rank[site, lab]
        )
        return problem.x[lab, site] + preferred_sites + preferred_labs >= 1

    model.stability = pyo.Constraint(
        model.L, model.S, rule=stability_rule
    )

    model.egalitarian_score = pyo.Objective(
        expr=sum(
            (model.lab_rank[lab, site] + model.site_rank[site, lab])
            * model.x[lab, site]
            for lab in model.L
            for site in model.S
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.egalitarian_score))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}