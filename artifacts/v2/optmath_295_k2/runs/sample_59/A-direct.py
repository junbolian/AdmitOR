import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 6
    periods = list(range(1, T + 1))

    fixed_setup_cost = params["fixed_setup_cost"]
    variable_production_cost = params["variable_production_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    backlogging_cost = params["backlogging_cost"]
    demand = params["demand"]
    production_capacity = params["production_capacity"]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.T, domain=pyo.Binary)
    model.inv = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.back = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    def _obj(mdl):
        return (
            sum(fixed_setup_cost[i - 1] * mdl.setup[i] for i in mdl.T)
            + sum(variable_production_cost[i - 1] * mdl.produce[i] for i in mdl.T)
            + sum(inventory_holding_cost[i - 1] * mdl.inv[i] for i in mdl.T)
            + sum(backlogging_cost[i - 1] * mdl.back[i] for i in mdl.T)
        )

    model.total_cost = pyo.Objective(rule=_obj, sense=pyo.minimize)

    def _capacity(mdl, i):
        return mdl.produce[i] <= production_capacity * mdl.setup[i]

    model.capacity_con = pyo.Constraint(model.T, rule=_capacity)

    def _balance(mdl, i):
        if i == 1:
            return mdl.produce[i] - mdl.back[i] == demand[i - 1] + mdl.inv[i]
        return mdl.inv[i - 1] + mdl.produce[i] - mdl.back[i - 1] == demand[i - 1] + mdl.inv[i] - mdl.back[i]

    model.balance = pyo.Constraint(model.T, rule=_balance)

    def _inv_final(mdl):
        return mdl.inv[T] == 0

    model.inv_final = pyo.Constraint(rule=_inv_final)

    def _back_final(mdl):
        return mdl.back[T] == 0

    model.back_final = pyo.Constraint(rule=_back_final)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}