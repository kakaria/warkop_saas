class BusinessRuleViolation(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class ProductAlreadyExistsError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class StockMovementCreationError(Exception):
    pass
