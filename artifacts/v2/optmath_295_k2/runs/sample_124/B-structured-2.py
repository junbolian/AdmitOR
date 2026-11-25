# IR: {"sets":{"individuals":"0..7","projects":"0..7"},"params":{"supply":"nonnegative vector indexed by individuals","demand":"nonnegative vector indexed by projects","capacity_limits":"nonnegative 8x8 matrix","costs":"real 8x8 matrix"},"variables":{"allocation[i,j]":{"type":"continuous","lower_bound":0}},"constraints":["For each individual i: sum_j allocation[i,j] == supply[i]","For each project j: sum_i allocation[i,j] == demand[j]","For each pair (i,j): allocation[i,j] <= capacity_limits[i,j]"],"objective":"minimize sum_i sum_j costs[i,j] * allocation[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]
    costs = params["costs"]

    model = pyo.ConcreteModel()
    model.individuals = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.individuals,
        initialize={i: supply[i] for i in model.individuals},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.projects,
        initialize={j: demand[j] for j in model.projects},
        within=pyo.NonNegativeReals,
    )
    model.capacity_limits = pyo.Param(
        model.individuals,
        model.projects,
        initialize={
            (i, j): capacity_limits[i][j]
            for i in model.individuals
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )
    model.costs = pyo.Param(
        model.individuals,
        model.projects,
        initialize={
            (i, j): costs[i][j]
            for i in model.individuals
            for j in model.projects
        },
        within=pyo.Reals,
    )

    model.allocation = pyo.Var(
        model.individuals,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mod, i):
        return (
            sum(mod.allocation[i, j] for j in mod.projects)
            == mod.supply[i]
        )

    def demand_rule(mod, j):
        return (
            sum(mod.allocation[i, j] for i in mod.individuals)
            == mod.demand[j]
        )

    def capacity_rule(mod, i, j):
        return mod.allocation[i, j] <= mod.capacity_limits[i, j]

    model.supply_balance = pyo.Constraint(
        model.individuals, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.projects, rule=demand_rule
    )
    model.assignment_capacity = pyo.Constraint(
        model.individuals, model.projects, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[i, j] * model.allocation[i, j]
            for i in model.individuals
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}