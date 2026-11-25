# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4]},"params":{},"data":{"investor_preferences":[[0,2,3,1,4],[1,4,2,0,3],[3,1,0,4,2],[0,4,2,1,3],[2,0,1,3,4]],"founder_preferences":[[4,1,3,2,0],[0,3,1,2,4],[3,1,2,0,4],[2,1,4,0,3],[1,4,0,3,2]]},"derived":{"rI[i,j]":"zero-based position of j in investor_preferences[i]","rF[j,i]":"zero-based position of i in founder_preferences[j]"},"variables":{"x[i,j]":"binary; 1 iff investor i matches founder j"},"constraints":["sum(j in J) x[i,j] = 1 for each i in I","sum(i in I) x[i,j] = 1 for each j in J","x[i,j] + sum(k in J: rI[i,k] < rI[i,j]) x[i,k] + sum(h in I: rF[j,h] < rF[j,i]) x[h,j] >= 1 for each (i,j) in I x J"],"objective":"minimize sum(i in I,j in J) (rI[i,j] + rF[j,i])*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # PARAMS is empty; all preference lists are fixed problem data.
    investor_preferences = (
        (0, 2, 3, 1, 4),
        (1, 4, 2, 0, 3),
        (3, 1, 0, 4, 2),
        (0, 4, 2, 1, 3),
        (2, 0, 1, 3, 4),
    )
    founder_preferences = (
        (4, 1, 3, 2, 0),
        (0, 3, 1, 2, 4),
        (3, 1, 2, 0, 4),
        (2, 1, 4, 0, 3),
        (1, 4, 0, 3, 2),
    )

    investor_rank = {
        (i, j): position
        for i, preferences in enumerate(investor_preferences)
        for position, j in enumerate(preferences)
    }
    founder_rank = {
        (j, i): position
        for j, preferences in enumerate(founder_preferences)
        for position, i in enumerate(preferences)
    }

    model = pyo.ConcreteModel()
    model.investors = pyo.RangeSet(0, 4)
    model.founders = pyo.RangeSet(0, 4)

    model.x = pyo.Var(
        model.investors,
        model.founders,
        domain=pyo.Binary,
    )

    def investor_assignment_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.founders) == 1

    model.investor_assignment = pyo.Constraint(
        model.investors,
        rule=investor_assignment_rule,
    )

    def founder_assignment_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.investors) == 1

    model.founder_assignment = pyo.Constraint(
        model.founders,
        rule=founder_assignment_rule,
    )

    def stability_rule(mod, i, j):
        return (
            mod.x[i, j]
            + sum(
                mod.x[i, k]
                for k in mod.founders
                if investor_rank[i, k] < investor_rank[i, j]
            )
            + sum(
                mod.x[h, j]
                for h in mod.investors
                if founder_rank[j, h] < founder_rank[j, i]
            )
            >= 1
        )

    model.stability = pyo.Constraint(
        model.investors,
        model.founders,
        rule=stability_rule,
    )

    model.total_misfit = pyo.Objective(
        expr=sum(
            (investor_rank[i, j] + founder_rank[j, i]) * model.x[i, j]
            for i in model.investors
            for j in model.founders
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        # Continue to objective retrieval, which determines success.

    try:
        obj_val = float(pyo.value(model.total_misfit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}