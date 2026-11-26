import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sell_table = params["sell_table"]
    sell_chair = params["sell_chair"]
    sell_bookshelf = params["sell_bookshelf"]
    cost_table = params["cost_table"]
    cost_chair = params["cost_chair"]
    cost_bookshelf = params["cost_bookshelf"]
    space_table = params["space_table"]
    space_chair = params["space_chair"]
    space_bookshelf = params["space_bookshelf"]
    space_capacity = params["space_capacity"]
    min_tables = params["min_tables"]
    min_bookshelves = params["min_bookshelves"]
    max_items = params["max_items"]

    profit_table = sell_table - cost_table
    profit_chair = sell_chair - cost_chair
    profit_bookshelf = sell_bookshelf - cost_bookshelf

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    tables = model.addVar(vtype=GRB.INTEGER, lb=0, name="tables")
    chairs = model.addVar(vtype=GRB.INTEGER, lb=0, name="chairs")
    bookshelves = model.addVar(vtype=GRB.INTEGER, lb=0, name="bookshelves")

    model.setObjective(
        profit_table * tables + profit_chair * chairs + profit_bookshelf * bookshelves,
        GRB.MAXIMIZE
    )

    model.addConstr(space_table * tables + space_chair * chairs + space_bookshelf * bookshelves <= space_capacity, "space")
    model.addConstr(tables >= min_tables, "min_tables")
    model.addConstr(bookshelves >= min_bookshelves, "min_bookshelves")
    model.addConstr(tables + chairs + bookshelves <= max_items, "max_items")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}