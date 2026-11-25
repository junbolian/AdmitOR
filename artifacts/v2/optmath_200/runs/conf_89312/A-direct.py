import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 5

    demand = params["demand"]
    production_cost = params["production_cost"]
    inventory_cost = params["inventory_cost"]
    backlog_cost = params["backlog_cost"]
    setup_cost = params["setup_cost"]
    production_capacity = params["production_capacity"]

    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(1, T)

    model.OrderedAmount = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.EndingInventory = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.BloggedAmount = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.OrderIsPlaced = pyo.Var(model.T, domain=pyo.Binary)

    def obj_rule(m):
        return (
            sum(production_cost[t - 1] * m.OrderedAmount[t] for t in m.T)
            + sum(inventory_cost[t - 1] * m.EndingInventory[t] for t in m.T)
            + sum(backlog_cost[t - 1] * m.BloggedAmount[t] for t in m.T)
            + sum(setup_cost[t - 1] * m.OrderIsPlaced[t] for t in m.T)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand fulfillment: inventory balance for each month
    # Net inventory change: prod + prev_inv - prev_backlog - demand = inv - backlog
    def balance_rule(m, t):
        if t == 1:
            return m.OrderedAmount[t] - demand[t - 1] == m.EndingInventory[t] - m.BloggedAmount[t]
        return (m.OrderedAmount[t] + m.EndingInventory[t - 1] - m.BloggedAmount[t - 1] - demand[t - 1]
                == m.EndingInventory[t] - m.BloggedAmount[t])

    model.demand_balance = pyo.Constraint(model.T, rule=balance_rule)

    # No ending inventory at the end of month 5
    model.no_final_inventory = pyo.Constraint(expr=model.EndingInventory[T] == 0)

    # No backlog at the end of month 5
    model.no_final_backlog = pyo.Constraint(expr=model.BloggedAmount[T] == 0)

    # Production capacity linking constraint
    def capacity_rule(m, t):
        return m.OrderedAmount[t] <= production_capacity * m.OrderIsPlaced[t]

    model.capacity_link = pyo.Constraint(model.T, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}