# IR: {"sets":{"K":"0,...,n","I":"1,...,n"},"params":{"mass":"params['m']","height":"params['H']","duration":"params['T']","thrust_bound":"params['b']","gravity":"params['g']","intervals":"params['n']","dt":"duration/intervals"},"variables":{"y[k]":"nonnegative continuous, k in K","v[k]":"real continuous, k in K","u[k]":"continuous in [0,thrust_bound], k in I"},"constraints":["y[0]=0","v[0]=0","v[k]=v[k-1]+dt*(u[k]/mass-gravity), k in I","y[k]=y[k-1]+dt*v[k-1]+dt^2*(u[k]/mass-gravity)/2, k in I","y[n]>=height"],"objective":"minimize dt*sum(u[k] for k in I)"}
#
# Assumptions: launch from rest; constant thrust within each interval;
# no prescribed terminal velocity; all supplied quantities use SI units.
#
# The objective is thrust impulse, a standard linear fuel-consumption proxy.
# Mechanical energy consumption is not generally linear in these variables.
#
# A physically infeasible instance must return a failure status. In particular,
# if thrust_bound < mass*gravity, this rocket cannot lift off from rest.
# The supplied thrust and mass therefore cannot support launch under ordinary
# Earth gravity. Increasing thrust or changing the physical data is necessary;
# changing the solver cannot make that instance feasible.
#
# Supply every parameter, including gravity, through params. No example data
# are substituted, and no function call is performed at module import.

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    mass = float(params["m"])
    height = float(params["H"])
    duration = float(params["T"])
    thrust_bound = float(params["b"])
    gravity = float(params["g"])
    intervals_raw = params["n"]

    physical_values = (mass, height, duration, thrust_bound, gravity)
    if not all(math.isfinite(value) for value in physical_values):
        return {"objective": None, "status": "invalid_parameter"}

    try:
        intervals = int(intervals_raw)
    except (ValueError, TypeError, OverflowError):
        return {"objective": None, "status": "invalid_n"}

    if intervals <= 0 or intervals != intervals_raw:
        return {"objective": None, "status": "invalid_n"}
    if mass <= 0 or duration <= 0:
        return {"objective": None, "status": "invalid_mass_or_time"}
    if height < 0 or thrust_bound < 0 or gravity < 0:
        return {"objective": None, "status": "invalid_physical_parameter"}

    model = pyo.ConcreteModel()

    model.K = pyo.RangeSet(0, intervals)
    model.I = pyo.RangeSet(1, intervals)

    model.mass = pyo.Param(initialize=mass)
    model.height_requirement = pyo.Param(initialize=height)
    model.duration = pyo.Param(initialize=duration)
    model.thrust_bound = pyo.Param(initialize=thrust_bound)
    model.gravity = pyo.Param(initialize=gravity)
    model.interval_count = pyo.Param(initialize=intervals)
    model.dt = pyo.Expression(expr=model.duration / model.interval_count)

    model.y = pyo.Var(model.K, domain=pyo.NonNegativeReals)
    model.v = pyo.Var(model.K, domain=pyo.Reals)
    model.u = pyo.Var(
        model.I,
        domain=pyo.NonNegativeReals,
        bounds=(0, thrust_bound),
    )

    model.initial_height = pyo.Constraint(expr=model.y[0] == 0)
    model.initial_velocity = pyo.Constraint(expr=model.v[0] == 0)

    def velocity_rule(instance, k):
        return instance.v[k] == (
            instance.v[k - 1]
            + instance.dt * (instance.u[k] / instance.mass - instance.gravity)
        )

    def height_rule(instance, k):
        return instance.y[k] == (
            instance.y[k - 1]
            + instance.dt * instance.v[k - 1]
            + instance.dt**2
            * (instance.u[k] / instance.mass - instance.gravity)
            / 2
        )

    model.velocity_dynamics = pyo.Constraint(model.I, rule=velocity_rule)
    model.height_dynamics = pyo.Constraint(model.I, rule=height_rule)
    model.required_terminal_height = pyo.Constraint(
        expr=model.y[intervals] >= model.height_requirement
    )

    model.total_thrust_impulse = pyo.Objective(
        expr=model.dt * sum(model.u[k] for k in model.I),
        sense=pyo.minimize,
    )

    # Constant maximum thrust gives an upper bound on terminal height.
    # Negative maximum acceleration also contradicts nonnegative altitude
    # immediately after launch, even if the required terminal height is zero.
    maximum_acceleration = thrust_bound / mass - gravity
    maximum_terminal_height = maximum_acceleration * duration**2 / 2
    provably_infeasible = (
        maximum_acceleration < 0 or maximum_terminal_height < height
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this specific error when automatic solution loading
        # fails because no feasible solution is available.
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        failure_reason = (
            "infeasible" if provably_infeasible else "no_feasible_solution"
        )

    # Objective retrieval alone determines success; no termination enums.
    try:
        obj_val = float(pyo.value(model.total_thrust_impulse))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}