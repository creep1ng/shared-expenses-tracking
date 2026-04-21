from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import ScheduledPayment, ScheduledPaymentFrequency, Transaction, TransactionType

logger = logging.getLogger(__name__)


# Creador de sesión async para el worker
def create_async_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    )
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async_session_factory = create_async_session_factory()


async def process_scheduled_payments(ctx: dict[str, Any]) -> None:
    """Procesa todos los pagos programados vencidos y crea las transacciones correspondientes."""
    logger.info("Starting scheduled payments processing job")

    now = datetime.now(UTC)
    processed_count = 0

    async with async_session_factory() as session:
        result = await session.execute(
            select(ScheduledPayment)
            .where(
                ScheduledPayment.is_active.is_(True),
                ScheduledPayment.next_due_date <= now,
            )
            .order_by(ScheduledPayment.next_due_date)
            .with_for_update()
        )

        payments = result.scalars().all()

        for payment in payments:
            try:
                # Crear transacción real
                transaction = Transaction(
                    workspace_id=payment.workspace_id,
                    category_id=payment.category_id,
                    amount_minor=payment.amount_minor,
                    currency=payment.currency,
                    description=payment.description,
                    occurred_at=payment.next_due_date,
                    type=TransactionType.EXPENSE,  # Por defecto gasto, se puede extender luego
                    paid_by_user_id=None,
                    source_account_id=None,
                    destination_account_id=None,
                )
                session.add(transaction)

                # Calcular siguiente fecha de vencimiento
                if payment.frequency == ScheduledPaymentFrequency.DAILY:
                    next_date = payment.next_due_date + timedelta(days=1)
                elif payment.frequency == ScheduledPaymentFrequency.WEEKLY:
                    next_date = payment.next_due_date + timedelta(weeks=1)
                elif payment.frequency == ScheduledPaymentFrequency.MONTHLY:
                    # Avanzar un mes (aproximado, lógica mejorada posteriormente)
                    next_date = payment.next_due_date + timedelta(days=30)
                elif payment.frequency == ScheduledPaymentFrequency.YEARLY:
                    next_date = payment.next_due_date + timedelta(days=365)
                else:
                    # Frecuencia desconocida, desactivar pago
                    payment.is_active = False
                    next_date = payment.next_due_date

                # Actualizar estado del pago programado
                payment.last_executed_at = now
                payment.next_due_date = next_date

                processed_count += 1
                logger.info(f"Processed scheduled payment {payment.id}")

            except Exception as e:
                logger.error(
                    f"Failed to process scheduled payment {payment.id}: {e!s}", exc_info=True
                )
                await session.rollback()
                continue

        await session.commit()

    logger.info(f"Completed scheduled payments processing. Processed {processed_count} payments")


async def startup(ctx: dict[str, Any]) -> None:
    """Inicializa el contexto del worker al iniciar."""
    logger.info("Worker starting up")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Limpia recursos al apagar el worker."""
    logger.info("Worker shutting down")


class WorkerSettings:
    """Configuración principal del worker arq."""

    redis_settings = RedisSettings(host=get_settings().redis_host, port=get_settings().redis_port)
    on_startup = startup
    on_shutdown = shutdown

    functions: ClassVar[list[Any]] = [
        process_scheduled_payments,
    ]

    cron_jobs: ClassVar[list[Any]] = [
        cron(
            process_scheduled_payments,
            hour=0,
            minute=0,
            run_at_startup=False,
            unique=True,
        ),
    ]

    # Configuración de reintentos y timeouts
    max_tries = 3
    retry_delay = 30
    job_timeout = 300
    keep_result = 3600
