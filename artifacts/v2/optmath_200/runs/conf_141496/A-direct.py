import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_projects = int(params["num_projects"])
    num_teams = int(params["num_teams"])
    team_capacity = params["team_capacity"]
    workloads = [params[f"project_workload_{j}"] for j in range(num_projects)]

    projects = list(range(num_projects))
    teams = list(range(num_teams))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(projects, teams, domain=pyo.Binary)
    model.y = pyo.Var(teams, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[t] for t in teams), sense=pyo.minimize)

    model.assign_con = pyo.Constraint(
        projects, rule=lambda m, j: sum(m.x[j, t] for t in teams) == 1
    )

    model.capacity_con = pyo.Constraint(
        teams,
        rule=lambda m, t: sum(workloads[j] * m.x[j, t] for j in projects)
        <= team_capacity * m.y[t],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}