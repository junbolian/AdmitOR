import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_table = params["price_table"]
    price_chair = params["price_chair"]
    price_bookshelf = params["price_bookshelf"]
    cost_table = params["cost_table"]
    cost_chair = params["cost_chair"]
    cost_bookshelf = params["cost_bookshelf"]
    space_table = params["space_table"]
    space_chair = params["space_chair"]
    space_bookshelf = params["space_bookshelf"]
    space_capacity = params["space_capacity"]
    min_tables = params["min_tables"]
    min_bookshelves = params["min_bookshelves"]
    max_total_items = params["max_total_items"]

    profit_table = price_table - cost_table
    profit_chair = price_chair - cost_chair
    profit_bookshelf = price_bookshelf - cost_bookshelf

    model = gp.Model("furniture_factory")
    model.setParam("OutputFlag", 0)

    tables = model.addVar(lb=0, vtype=GRB.INTEGER, name="tables")
    chairs = model.addVar(lb=0, vtype=GRB.INTEGER, name="chairs")
    bookshelves = model.addVar(lb=0, vtype=GRB.INTEGER, name="bookshelves")

    model.setObjective(
        profit_table * tables + profit_chair * chairs + profit_bookshelf * bookshelves,
        GRB.MAXIMIZE
    )

    model.addConstr(
        space_table * tables + space_chair * chairs + space_bookshelf * bookshelves <= space_capacity,
        name="warehouse_space"
    )
    model.addConstr(tables >= min_tables, name="min_tables")
    model.addConstr(bookshelves >= min_bookshelves, name="min_bookshelves")
    model.addConstr(tables + chairs + bookshelves <= max_total_items, name="max_total_items")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}