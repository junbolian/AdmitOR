import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost_matrix"]
    n_teams = len(cost)
    n_sites = len(cost[0])
    teams = range(n_teams)
    sites = range(n_sites)

    model = pyo.ConcreteModel()
    model.TEAMS = pyo.Set(initialize=list(teams))
    model.SITES = pyo.Set(initialize=list(sites))

    model.x = pyo.Var(model.TEAMS, model.SITES, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    def team_rule(m, t):
        return sum(m.x[t, s] for s in m.SITES) == 1
    model.team_con = pyo.Constraint(model.TEAMS, rule=team_rule)

    def site_rule(m, s):
        return sum(m.x[t, s] for t in m.TEAMS) == 1
    model.site_con = pyo.Constraint(model.SITES, rule=site_rule)

    def makespan_rule(m, t, s):
        return m.z >= cost[t][s] * m.x[t, s]
    model.makespan_con = pyo.Constraint(model.TEAMS, model.SITES, rule=makespan_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}