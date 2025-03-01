# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.admin import Admin  # noqa
from app.models.merchant import Merchant  # noqa
from app.models.payment import Payment  # noqa