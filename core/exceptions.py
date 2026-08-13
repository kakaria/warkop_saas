from django.db.models.functions import Exp


class BussinessRuleViolation(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class StockMovementCreationError(Exception):
    pass


class InsufficientStockError(Exception):
    pass
