# IR: {"sets":{"I":[0,1,2,3,4],"F":[0,1,2,3,4]},"params":{"investor_rankings":"params['investor_rankings']; each row is a permutation of F","founder_rankings":"params['founder_rankings']; each row is a permutation of I","investor_rank[i,f]":"zero-based position of f in investor_rankings[i]","founder_rank[f,i]":"zero-based position of i in founder_rankings[f]"},"variables":{"x[i,f]":"binary; 1 iff investor i is matched with founder f"},"constraints":["For each i: sum_f x[i,f] = 1","For each f: sum_i x[i,f] = 1","For each (i,f): x[i,f] + sum_{g:investor_rank[i,g]<investor_rank[i,f]} x[i,g] + sum_{j:founder_rank[f,j]<founder_rank[f,i]} x[j,f] >= 1"],"objective":"minimize sum_{i,f} (investor_rank[i,f] + founder_rank[f,i])*x[i,f]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investors = range(5)
    founders = range(5)

    investor_rankings = params["investor_rankings"]
    founder_rankings = params["founder_rankings"]

    if len(investor_rankings) != len(investors):
        raise ValueError("Expected one ranking for each of five investors.")
    if len(founder_rankings) != len(founders):
        raise ValueError("Expected one ranking for each of five founders.")

    for investor in investors:
        ranking = investor_rankings[investor]
        if len(ranking) != len(founders) or set(ranking) != set(founders):
            raise ValueError(
                f"Investor {investor}'s ranking must be a permutation of 0 through 4."
            )

    for founder in founders:
        ranking = founder_rankings[founder]
        if len(ranking) != len(investors) or set(ranking) != set(investors):
            raise ValueError(
                f"Founder {founder}'s ranking must be a permutation of 0 through 4."
            )

    investor_positions = {
        (investor, founder): position
        for investor in investors
        for position, founder in enumerate(investor_rankings[investor])
    }
    founder_positions = {
        (founder, investor): position
        for founder in founders
        for position, investor in enumerate(founder_rankings[founder])
    }

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=investors, ordered=True)
    model.F = pyo.Set(initialize=founders, ordered=True)

    model.investor_rank = pyo.Param(
        model.I,
        model.F,
        initialize=investor_positions,
        within=pyo.NonNegativeIntegers,
    )
    model.founder_rank = pyo.Param(
        model.F,
        model.I,
        initialize=founder_positions,
        within=pyo.NonNegativeIntegers,
    )
    model.x = pyo.Var(model.I, model.F, domain=pyo.Binary)

    def investor_assignment_rule(instance, investor):
        return sum(instance.x[investor, founder] for founder in instance.F) == 1

    model.investor_assignment = pyo.Constraint(
        model.I, rule=investor_assignment_rule
    )

    def founder_assignment_rule(instance, founder):
        return sum(instance.x[investor, founder] for investor in instance.I) == 1

    model.founder_assignment = pyo.Constraint(
        model.F, rule=founder_assignment_rule
    )

    def stability_rule(instance, investor, founder):
        return (
            instance.x[investor, founder]
            + sum(
                instance.x[investor, other_founder]
                for other_founder in instance.F
                if investor_positions[investor, other_founder]
                < investor_positions[investor, founder]
            )
            + sum(
                instance.x[other_investor, founder]
                for other_investor in instance.I
                if founder_positions[founder, other_investor]
                < founder_positions[founder, investor]
            )
            >= 1
        )

    model.stability = pyo.Constraint(model.I, model.F, rule=stability_rule)

    model.total_misfit = pyo.Objective(
        expr=sum(
            (
                model.investor_rank[investor, founder]
                + model.founder_rank[founder, investor]
            )
            * model.x[investor, founder]
            for investor in model.I
            for founder in model.F
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_misfit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}