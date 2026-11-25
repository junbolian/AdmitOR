# IR: {"sets":{"I":[0,1,2,3,4],"F":[0,1,2,3,4]},"params":{"investor_rankings":"strict permutation of F for each i in I","founder_rankings":"strict permutation of I for each f in F","rI[i,f]":"zero-based position of f in investor_rankings[i]","rF[f,i]":"zero-based position of i in founder_rankings[f]"},"variables":{"x[i,f]":"binary; 1 iff investor i is matched with founder f"},"constraints":["For each i: sum_f x[i,f] = 1","For each f: sum_i x[i,f] = 1","For each (i,f): x[i,f] + sum_{g:rI[i,g]<rI[i,f]} x[i,g] + sum_{j:rF[f,j]<rF[f,i]} x[j,f] >= 1"],"objective":"minimize sum_{i,f} (rI[i,f] + rF[f,i])*x[i,f]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investor_rankings = params["investor_rankings"]
    founder_rankings = params["founder_rankings"]

    investors = range(5)
    founders = range(5)

    if len(investor_rankings) != 5 or len(founder_rankings) != 5:
        return {"objective": None, "status": "invalid_rankings"}

    expected = list(range(5))
    for investor in investors:
        if sorted(investor_rankings[investor]) != expected:
            return {"objective": None, "status": "invalid_rankings"}
    for founder in founders:
        if sorted(founder_rankings[founder]) != expected:
            return {"objective": None, "status": "invalid_rankings"}

    investor_rank = {
        (investor, founder): position
        for investor in investors
        for position, founder in enumerate(investor_rankings[investor])
    }
    founder_rank = {
        (founder, investor): position
        for founder in founders
        for position, investor in enumerate(founder_rankings[founder])
    }

    model = pyo.ConcreteModel()
    model.investors = pyo.Set(initialize=investors, ordered=True)
    model.founders = pyo.Set(initialize=founders, ordered=True)

    model.investor_rank = pyo.Param(
        model.investors,
        model.founders,
        initialize=investor_rank,
        within=pyo.NonNegativeIntegers,
    )
    model.founder_rank = pyo.Param(
        model.founders,
        model.investors,
        initialize=founder_rank,
        within=pyo.NonNegativeIntegers,
    )
    model.x = pyo.Var(
        model.investors, model.founders, domain=pyo.Binary
    )

    def investor_assignment_rule(instance, investor):
        return sum(
            instance.x[investor, founder] for founder in instance.founders
        ) == 1

    model.investor_assignment = pyo.Constraint(
        model.investors, rule=investor_assignment_rule
    )

    def founder_assignment_rule(instance, founder):
        return sum(
            instance.x[investor, founder] for investor in instance.investors
        ) == 1

    model.founder_assignment = pyo.Constraint(
        model.founders, rule=founder_assignment_rule
    )

    def stability_rule(instance, investor, founder):
        preferred_founders = sum(
            instance.x[investor, other_founder]
            for other_founder in instance.founders
            if investor_rank[investor, other_founder]
            < investor_rank[investor, founder]
        )
        preferred_investors = sum(
            instance.x[other_investor, founder]
            for other_investor in instance.investors
            if founder_rank[founder, other_investor]
            < founder_rank[founder, investor]
        )
        return (
            instance.x[investor, founder]
            + preferred_founders
            + preferred_investors
            >= 1
        )

    model.stability = pyo.Constraint(
        model.investors, model.founders, rule=stability_rule
    )

    model.total_misfit = pyo.Objective(
        expr=sum(
            (
                model.investor_rank[investor, founder]
                + model.founder_rank[founder, investor]
            )
            * model.x[investor, founder]
            for investor in model.investors
            for founder in model.founders
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_misfit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}