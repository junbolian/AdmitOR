# IR: {"sets":{"P":"range(num_projects)","T":"range(num_teams)"},"params":{"workload":"[project_workload_0,...,project_workload_6]","team_capacity":"params['team_capacity']","num_teams":"params['num_teams']","num_projects":"params['num_projects']"},"variables":{"x[p,t]":"binary: project p assigned to team t","y[t]":"binary: team t active"},"constraints":["For each p: sum(t in T, x[p,t]) = 1","For each t: sum(p in P, workload[p]*x[p,t]) <= team_capacity*y[t]","For each p,t: x[p,t] <= y[t]","For each t: y[t] <= sum(p in P, x[p,t])"],"objective":"minimize sum(t in T, y[t])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    workloads = [
        params["project_workload_0"],
        params["project_workload_1"],
        params["project_workload_2"],
        params["project_workload_3"],
        params["project_workload_4"],
        params["project_workload_5"],
        params["project_workload_6"],
    ]
    team_capacity = params["team_capacity"]
    num_teams = params["num_teams"]
    num_projects = params["num_projects"]

    if (
        int(num_teams) != num_teams
        or int(num_projects) != num_projects
        or num_teams < 0
        or not 0 <= num_projects <= len(workloads)
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=range(int(num_projects)), ordered=True)
    model.T = pyo.Set(initialize=range(int(num_teams)), ordered=True)

    model.workload = pyo.Param(
        model.P, initialize={p: workloads[p] for p in model.P}
    )
    model.capacity = pyo.Param(initialize=team_capacity)

    model.x = pyo.Var(model.P, model.T, domain=pyo.Binary)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    def assignment_rule(block, p):
        # Tuple form also represents infeasibility when no teams exist.
        return (1, sum(block.x[p, t] for t in block.T), 1)

    model.project_assignment = pyo.Constraint(model.P, rule=assignment_rule)

    def capacity_rule(block, t):
        return (
            sum(block.workload[p] * block.x[p, t] for p in block.P)
            <= block.capacity * block.y[t]
        )

    model.team_capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

    def activation_rule(block, p, t):
        return block.x[p, t] <= block.y[t]

    model.assignment_activation = pyo.Constraint(
        model.P, model.T, rule=activation_rule
    )

    def active_team_rule(block, t):
        return block.y[t] <= sum(block.x[p, t] for p in block.P)

    model.active_team_has_project = pyo.Constraint(
        model.T, rule=active_team_rule
    )

    model.total_teams = pyo.Objective(
        expr=sum(model.y[t] for t in model.T),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_teams))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}