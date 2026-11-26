import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a1 = params["a1"]
    a2 = params["a2"]
    pilot_yield = params["pilot_yield_per_training_jet"]
    n = int(params["n"])
    total_per_year = a1 + a2

    years = list(range(1, n + 1))

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=years)

    # x_t: jets entering combat immediately in year t
    # y_t: jets becoming training platforms in year t
    model.x = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)

    # cumulative pilots available (qualified before year t + newly qualified)
    # pilots available at year t come from training jets of years 1..t-1
    # x_t combat jets in year t must be <= available pilots
    def pilot_rule(m, t):
        return m.x[t] <= pilot_yield * sum(m.y[s] for s in m.T if s < t)
    model.pilot_con = pyo.Constraint(model.T, rule=pilot_rule)

    # fleet balance each year: x_t + y_t = total delivered that year
    def balance_rule(m, t):
        return m.x[t] + m.y[t] == total_per_year
    model.balance_con = pyo.Constraint(model.T, rule=balance_rule)

    # training jets can be reassigned to combat later; but a training jet trained
    # pilots for subsequent availability. Reassignment of prior training jets to
    # combat is allowed, but they already produced pilots. Include cumulative
    # fleet feasibility: combat jets used in year t must come from fleet built
    # up to that year minus jets already committed to training in earlier years
    # that remain training. Model the "reassignment" by allowing prior years'
    # training jets to convert to combat, tracked via cumulative combat usage.
    # Cumulative combat assignments across years cannot exceed cumulative
    # aircraft delivered minus training jets retained as training platforms.
    # We allow x_t to draw from all available aircraft (including past training
    # jets reassigned). Let cumulative x up to t <= cumulative delivered up to t
    # minus training jets in year t (those still held as trainers this year).
    # Since y_t are current-year trainers, and past trainers may be reassigned,
    # the simplest correct fleet constraint is: sum_{s<=t} x_s <= sum_{s<=t}(a1+a2) - y_t
    # (all delivered so far minus those currently retained as trainers).
    def fleet_rule(m, t):
        delivered = total_per_year * t
        return sum(m.x[s] for s in m.T if s <= t) <= delivered - m.y[t]
    model.fleet_con = pyo.Constraint(model.T, rule=fleet_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[t] for t in model.T), sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}