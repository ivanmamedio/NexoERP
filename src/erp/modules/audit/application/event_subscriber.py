"""EventBus subscriber that writes audit log entries from domain events."""

from __future__ import annotations

from erp.modules.audit.application.services import AuditService
from erp.shared.application.events import EventBus
from erp.shared.domain.events import (
    DomainEvent,
    EntityCreated,
    EntityDeleted,
    EntityUpdated,
    SaleCompleted,
    UserLoggedIn,
)


class AuditEventSubscriber:
    """Subscribes to domain events and persists them to the audit log."""

    def __init__(self, event_bus: EventBus, audit_service: AuditService) -> None:
        self._event_bus = event_bus
        self._audit_service = audit_service
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(EntityCreated, self._on_entity_created)
        self._event_bus.subscribe(EntityUpdated, self._on_entity_updated)
        self._event_bus.subscribe(EntityDeleted, self._on_entity_deleted)
        self._event_bus.subscribe(UserLoggedIn, self._on_user_logged_in)
        self._event_bus.subscribe(SaleCompleted, self._on_sale_completed)

    def _on_entity_created(self, event: EntityCreated) -> None:
        self._audit_service.log_event(
            user_id=event.user_id,
            username=event.username,
            action=f"{event.entity_type}.create",
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            before={},
            after=event.after,
        )

    def _on_entity_updated(self, event: EntityUpdated) -> None:
        self._audit_service.log_event(
            user_id=event.user_id,
            username=event.username,
            action=f"{event.entity_type}.update",
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            before=event.before,
            after=event.after,
        )

    def _on_entity_deleted(self, event: EntityDeleted) -> None:
        self._audit_service.log_event(
            user_id=event.user_id,
            username=event.username,
            action=f"{event.entity_type}.delete",
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            before=event.before,
            after={},
        )

    def _on_user_logged_in(self, event: UserLoggedIn) -> None:
        self._audit_service.log_event(
            user_id=event.user_id,
            username=event.username,
            action="user.login",
            entity_type="User",
            entity_id=event.user_id,
            before={},
            after={},
        )

    def _on_sale_completed(self, event: SaleCompleted) -> None:
        self._audit_service.log_event(
            user_id=event.user_id,
            username=event.username,
            action="sale.completed",
            entity_type="Sale",
            entity_id=event.sale_id,
            before={},
            after={
                "total_cents": event.total_cents,
                "cash_cents": event.cash_cents,
                "pix_cents": event.pix_cents,
                "card_cents": event.card_cents,
                "session_id": event.session_id,
            },
        )

    def handle(self, event: DomainEvent) -> None:
        """Generic handler entry point for manual dispatch."""
        self._event_bus.publish(event)
