from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.workspaces import get_workspace_service
from app.core.config import Settings, get_settings
from app.core.storage import InMemoryObjectStorage, ObjectStorage, S3ObjectStorage
from app.db.session import get_db_session
from app.services.transactions import TransactionService
from app.services.workspaces import WorkspaceService

_TEST_OBJECT_STORAGE = InMemoryObjectStorage()


def get_object_storage(settings: Settings = Depends(get_settings)) -> ObjectStorage:
    if settings.app_env == "test":
        return _TEST_OBJECT_STORAGE
    return S3ObjectStorage(settings)


def get_transaction_service(
    session: Session = Depends(get_db_session),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    settings: Settings = Depends(get_settings),
    object_storage: ObjectStorage = Depends(get_object_storage),
) -> TransactionService:
    return TransactionService(
        session=session,
        workspace_service=workspace_service,
        settings=settings,
        object_storage=object_storage,
    )
